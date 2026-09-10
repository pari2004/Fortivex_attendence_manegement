"""
ats_shortlisting/views.py

Native re-implementation of the reference "ATS Resume Shortlisting Tool"
(Streamlit) inside FAMS. The scoring/parsing engine (ats_shortlisting.engine)
is ported near-verbatim from the reference tool; this module replaces its
Streamlit UI + Applicants.xlsx persistence with Django views/templates and
real DB models (ats_shortlisting.models).
"""

import json
import logging
import os
import tempfile
import threading
import uuid
from collections import Counter
from pathlib import Path

from django.contrib import messages
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from openpyxl import Workbook

from ats_shortlisting.decorators import admin_or_superuser_required
from ats_shortlisting.engine import ats_scoring, resume_parser
from ats_shortlisting.engine.drive_utils import DriveFetchError, fetch_pdfs_from_drive
from ats_shortlisting.forms import CandidateFilterForm, JobDescriptionForm
from ats_shortlisting.models import ATSCandidate, ATSJobDescription
from horilla.decorators import hx_request_required, login_required

logger = logging.getLogger("ats_shortlisting")

EXPERIENCE_BUCKETS = [
    ("0-1", 0, 1), ("1-2", 1, 2), ("2-3", 2, 3), ("3-5", 3, 5),
    ("5-8", 5, 8), ("8-12", 8, 12), ("12+", 12, 999),
]

IMPORT_PROGRESS_TIMEOUT = 1800


def _progress_key(run_id: str) -> str:
    return f"ats_import_progress:{run_id}"


def _has_drive_credentials() -> bool:
    return bool(
        os.environ.get("GOOGLE_DRIVE_API_KEY") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )


def _normalize_phone(phone: str) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def _find_existing_candidate(resume_hash: str, email: str, phone: str):
    """Same 3-tier precedence as the reference tool's
    excel_store.find_existing_candidate: exact resume hash, then email, then
    phone. Returns (candidate_or_None, match_reason)."""
    if resume_hash:
        match = ATSCandidate.objects.filter(resume_hash=resume_hash).first()
        if match:
            return match, "hash"
    if email:
        match = ATSCandidate.objects.filter(email__iexact=email.strip()).first()
        if match:
            return match, "email"
    phone_norm = _normalize_phone(phone)
    if phone_norm:
        for candidate in ATSCandidate.objects.exclude(phone=""):
            if _normalize_phone(candidate.phone) == phone_norm:
                return candidate, "phone"
    return None, ""


def _process_one_file(
    filename, file_bytes, jd, weights, shortlist_threshold, maybe_threshold,
    staging_dir, jd_record, drive_meta=None,
):
    text, is_scanned, ok = resume_parser.extract_text(file_bytes, filename, staging_dir)
    if not ok:
        return {"file_name": filename, "status": "failed", "reason": _("Could not extract any text"), "ats_score": None}

    parsed = resume_parser.parse_resume(text, filename, is_scanned=is_scanned)
    result = ats_scoring.score_resume(
        parsed, jd, weights=weights,
        shortlist_threshold=shortlist_threshold, maybe_threshold=maybe_threshold,
    )

    existing, reason = _find_existing_candidate(parsed.resume_hash, parsed.email, parsed.phone)
    candidate = existing or ATSCandidate()

    role_suffix = ""
    if parsed.current_designation and parsed.current_company:
        role_suffix = f" ({parsed.current_designation} at {parsed.current_company})"
    elif parsed.current_designation or parsed.current_company:
        role_suffix = f" ({parsed.current_designation or parsed.current_company})"

    candidate.name = parsed.name
    candidate.email = parsed.email
    candidate.phone = parsed.phone
    candidate.experience_text = f"{parsed.total_experience_years} years{role_suffix}"
    candidate.total_experience_years = parsed.total_experience_years
    candidate.skills = ", ".join(parsed.skills)
    candidate.detected_job_domain = jd.domain
    candidate.education = "; ".join(parsed.education)
    candidate.ats_score = result.ats_score
    candidate.skill_match_pct = result.required_skill_match_pct
    candidate.experience_match_pct = result.experience_match_pct
    candidate.matched_skills = ", ".join(result.matched_required_skills + result.matched_preferred_skills)
    candidate.missing_skills = ", ".join(result.missing_required_skills)
    candidate.recommendation = result.recommendation
    candidate.recommendation_text = result.recommendation_text
    candidate.resume_hash = parsed.resume_hash
    candidate.resume_file_name = filename
    candidate.last_job_description = jd_record
    if drive_meta:
        candidate.google_drive_file_id = drive_meta.get("file_id", "")
        candidate.google_drive_url = drive_meta.get("url", "")
    candidate.resume.save(filename, ContentFile(file_bytes), save=False)
    candidate.save()

    if existing is None:
        status = "imported"
    elif reason == "hash":
        status = "rescored"
    else:
        status = "updated"

    return {"file_name": filename, "status": status, "ats_score": result.ats_score, "candidate_id": candidate.id, "reason": ""}


def _dashboard_context(request):
    filter_form = CandidateFilterForm(request.GET or None)

    candidates = ATSCandidate.objects.all()
    rec_filter = request.GET.getlist("recommendation")
    if rec_filter:
        candidates = candidates.filter(recommendation__in=rec_filter)
    min_score = request.GET.get("min_score")
    if min_score:
        try:
            candidates = candidates.filter(ats_score__gte=float(min_score))
        except ValueError:
            pass
    domain = request.GET.get("domain")
    if domain:
        candidates = candidates.filter(detected_job_domain=domain)
    search = request.GET.get("search")
    if search:
        candidates = candidates.filter(Q(name__icontains=search) | Q(email__icontains=search))

    all_candidates = ATSCandidate.objects.all()
    total = all_candidates.count()
    shortlisted = all_candidates.filter(recommendation="Shortlist").count()
    rejected = all_candidates.filter(recommendation="Reject").count()
    avg_score = all_candidates.aggregate(avg=Avg("ats_score"))["avg"] or 0

    domains = sorted(
        all_candidates.exclude(detected_job_domain="")
        .order_by()
        .values_list("detected_job_domain", flat=True)
        .distinct()
    )

    skill_counter, missing_counter = Counter(), Counter()
    for skills_csv in all_candidates.exclude(skills="").values_list("skills", flat=True):
        skill_counter.update(s.strip() for s in skills_csv.split(",") if s.strip())
    for missing_csv in all_candidates.exclude(missing_skills="").values_list("missing_skills", flat=True):
        missing_counter.update(s.strip() for s in missing_csv.split(",") if s.strip())

    top_skills = skill_counter.most_common(10)
    top_missing = missing_counter.most_common(10)

    bucket_counts = [0] * len(EXPERIENCE_BUCKETS)
    for years in all_candidates.values_list("total_experience_years", flat=True):
        for i, (_label, lo, hi) in enumerate(EXPERIENCE_BUCKETS):
            if lo <= years < hi:
                bucket_counts[i] += 1
                break

    return {
        "candidates": candidates.order_by("-ats_score"),
        "filter_form": filter_form,
        "total_candidates": total,
        "shortlisted_count": shortlisted,
        "rejected_count": rejected,
        "avg_score": round(avg_score, 1),
        "domains": domains,
        "skill_labels": json.dumps([s for s, _c in top_skills]),
        "skill_counts": json.dumps([c for _s, c in top_skills]),
        "missing_labels": json.dumps([s for s, _c in top_missing]),
        "missing_counts": json.dumps([c for _s, c in top_missing]),
        "exp_labels": json.dumps([b[0] for b in EXPERIENCE_BUCKETS]),
        "exp_counts": json.dumps(bucket_counts),
        "has_candidates": total > 0,
        "has_drive_credentials": _has_drive_credentials(),
    }


@login_required
@admin_or_superuser_required
def ats_home(request):
    context = {"form": JobDescriptionForm(), **_dashboard_context(request)}
    return render(request, "ats_shortlisting/home.html", context)


@login_required
@admin_or_superuser_required
@hx_request_required
def ats_analyze_jd(request):
    jd_text = request.POST.get("jd_text", "")
    detected = ats_scoring.analyze_job_description(jd_text) if jd_text.strip() else None
    initial = {"jd_text": jd_text}
    if detected:
        initial.update({
            "required_skills": ", ".join(detected.required_skills),
            "preferred_skills": ", ".join(detected.preferred_skills),
            "min_experience_years": detected.min_experience_years,
            "preferred_experience_years": detected.preferred_experience_years,
            "education_requirement": detected.education_requirement,
            "certifications_required": ", ".join(detected.certifications_required),
        })
    form = JobDescriptionForm(initial=initial)
    return render(request, "ats_shortlisting/partials/_jd_analysis.html", {"form": form, "detected": detected})


def _execute_import(
    files_map, drive_link, jd, weights, shortlist_threshold, maybe_threshold, jd_record, progress_cb=None,
):
    """Runs the fetch(optional)+parse+score+upsert pipeline for one batch.
    ``progress_cb(done, total, filename, outcomes, counts, drive_warnings)`` is
    called once before the loop (done=0) and once after every file, mirroring
    the reference tool's ``progress_cb`` contract so the same shape can drive
    either an inline render (no callback) or a background thread reporting
    into the cache (callback)."""
    drive_warnings = []
    drive_meta_map = {}
    if drive_link:
        try:
            fetch_result = fetch_pdfs_from_drive(drive_link)
            files_map = dict(files_map)
            files_map.update(dict(fetch_result))
            drive_meta_map = fetch_result.file_meta
            drive_warnings.extend(fetch_result.warnings)
        except DriveFetchError as e:
            drive_warnings.append(str(e))

    total = len(files_map)
    outcomes = []
    counts = {"imported": 0, "updated": 0, "rescored": 0, "failed": 0}

    if progress_cb:
        progress_cb(0, total, "", outcomes, counts, drive_warnings)

    with tempfile.TemporaryDirectory() as staging_dir_str:
        staging_dir = Path(staging_dir_str)
        for i, (filename, file_bytes) in enumerate(files_map.items(), start=1):
            try:
                outcome = _process_one_file(
                    filename, file_bytes, jd, weights, shortlist_threshold, maybe_threshold,
                    staging_dir, jd_record, drive_meta_map.get(filename),
                )
            except Exception as e:  # noqa: BLE001 - one bad file must not abort the batch
                logger.exception("ATS import failed for %s", filename)
                outcome = {"file_name": filename, "status": "failed", "reason": str(e), "ats_score": None}
            counts[outcome["status"]] = counts.get(outcome["status"], 0) + 1
            outcomes.append(outcome)
            if progress_cb:
                progress_cb(i, total, filename, outcomes, counts, drive_warnings)

    return {
        "total_files": total,
        "counts": counts,
        "outcomes": outcomes,
        "drive_warnings": drive_warnings,
        "domain": jd.domain,
    }


def _run_import_async(run_id, files_map, drive_link, jd, weights, shortlist_threshold, maybe_threshold, jd_record_id):
    """Executed on a background thread so the browser can poll progress
    instead of blocking on one long request, mirroring the reference tool's
    live progress bar (there, Streamlit's own rerun/websocket loop provided
    that; here it's cache-backed polling)."""
    key = _progress_key(run_id)
    try:
        jd_record = ATSJobDescription.objects.get(id=jd_record_id)

        def progress_cb(done, total, filename, outcomes, counts, drive_warnings):
            cache.set(key, {
                "done": False, "processed": done, "total": total, "current_file": filename,
                "counts": dict(counts), "outcomes": list(outcomes), "drive_warnings": list(drive_warnings),
            }, timeout=IMPORT_PROGRESS_TIMEOUT)

        report = _execute_import(
            files_map, drive_link, jd, weights, shortlist_threshold, maybe_threshold,
            jd_record, progress_cb=progress_cb,
        )
        cache.set(key, {"done": True, "processed": report["total_files"], **report}, timeout=IMPORT_PROGRESS_TIMEOUT)
    except Exception:  # noqa: BLE001 - background thread must never crash silently
        logger.exception("ATS async import crashed for run %s", run_id)
        cache.set(key, {
            "done": True, "processed": 0, "total_files": 0, "counts": {}, "outcomes": [],
            "drive_warnings": [str(_("Import failed unexpectedly. Check server logs."))], "domain": "",
        }, timeout=IMPORT_PROGRESS_TIMEOUT)
    finally:
        from django.db import connections
        connections.close_all()


def _build_jd_and_weights(cleaned):
    detected = ats_scoring.analyze_job_description(cleaned["jd_text"])
    required_skills = [s.strip().lower() for s in cleaned.get("required_skills", "").split(",") if s.strip()]
    preferred_skills = [s.strip().lower() for s in cleaned.get("preferred_skills", "").split(",") if s.strip()]
    certifications_required = [s.strip().lower() for s in cleaned.get("certifications_required", "").split(",") if s.strip()]

    jd = ats_scoring.JobDescription(
        raw_text=cleaned["jd_text"],
        title=detected.title,
        domain=detected.domain,
        required_skills=required_skills or detected.required_skills,
        preferred_skills=preferred_skills or detected.preferred_skills,
        soft_skills=detected.soft_skills,
        min_experience_years=cleaned.get("min_experience_years") or 0.0,
        preferred_experience_years=cleaned.get("preferred_experience_years") or 0.0,
        education_requirement=cleaned.get("education_requirement") or "",
        certifications_required=certifications_required or detected.certifications_required,
        keywords=detected.keywords,
        responsibilities=detected.responsibilities,
    )
    weights = ats_scoring.ScoringWeights(
        required_skills=cleaned["weight_required_skills"],
        preferred_skills=cleaned["weight_preferred_skills"],
        experience=cleaned["weight_experience"],
        education=cleaned["weight_education"],
        certifications=cleaned["weight_certifications"],
        resume_quality=cleaned["weight_resume_quality"],
    )
    return jd, weights


def _create_jd_record(jd, weights, shortlist_threshold, maybe_threshold):
    return ATSJobDescription.objects.create(
        raw_text=jd.raw_text, title=jd.title, domain=jd.domain,
        required_skills=", ".join(jd.required_skills),
        preferred_skills=", ".join(jd.preferred_skills),
        soft_skills=", ".join(jd.soft_skills),
        min_experience_years=jd.min_experience_years,
        preferred_experience_years=jd.preferred_experience_years,
        education_requirement=jd.education_requirement,
        certifications_required=", ".join(jd.certifications_required),
        keywords=", ".join(jd.keywords),
        responsibilities="\n".join(jd.responsibilities),
        weight_required_skills=weights.required_skills,
        weight_preferred_skills=weights.preferred_skills,
        weight_experience=weights.experience,
        weight_education=weights.education,
        weight_certifications=weights.certifications,
        weight_resume_quality=weights.resume_quality,
        shortlist_threshold=shortlist_threshold,
        maybe_threshold=maybe_threshold,
    )


@login_required
@admin_or_superuser_required
def ats_run_import(request):
    is_htmx = request.headers.get("HX-Request") == "true"
    if request.method != "POST":
        return redirect("ats-tool-home")

    form = JobDescriptionForm(request.POST)
    if not form.is_valid():
        context = {"form": form, **_dashboard_context(request)}
        return render(request, "ats_shortlisting/home.html", context, status=400)

    cleaned = form.cleaned_data
    files = request.FILES.getlist("resumes")
    drive_link = (cleaned.get("drive_link") or "").strip()

    if not files and not drive_link:
        messages.error(request, _("Upload at least one resume or provide a Google Drive folder link."))
        context = {"form": form, **_dashboard_context(request)}
        return render(request, "ats_shortlisting/home.html", context, status=400)

    if cleaned.get("replace_existing"):
        ATSCandidate.objects.all().delete()

    jd, weights = _build_jd_and_weights(cleaned)
    shortlist_threshold = cleaned["shortlist_threshold"]
    maybe_threshold = cleaned["maybe_threshold"]
    jd_record = _create_jd_record(jd, weights, shortlist_threshold, maybe_threshold)
    files_map = {f.name: f.read() for f in files}

    if is_htmx:
        run_id = uuid.uuid4().hex
        cache.set(_progress_key(run_id), {
            "done": False, "processed": 0, "total": 0, "current_file": "",
            "counts": {"imported": 0, "updated": 0, "rescored": 0, "failed": 0},
            "outcomes": [], "drive_warnings": [],
        }, timeout=IMPORT_PROGRESS_TIMEOUT)
        threading.Thread(
            target=_run_import_async,
            args=(run_id, files_map, drive_link, jd, weights, shortlist_threshold, maybe_threshold, jd_record.id),
            daemon=True,
        ).start()
        context = {"run_id": run_id, **_dashboard_context(request)}
        return render(request, "ats_shortlisting/partials/_import_progress.html", context)

    report = _execute_import(files_map, drive_link, jd, weights, shortlist_threshold, maybe_threshold, jd_record)
    run_id = uuid.uuid4().hex
    cache.set(_progress_key(run_id), {"done": True, "processed": report["total_files"], **report}, timeout=IMPORT_PROGRESS_TIMEOUT)
    report["run_id"] = run_id
    context = {"form": JobDescriptionForm(initial=cleaned), "report": report, **_dashboard_context(request)}
    messages.success(request, _("Import complete."))
    return render(request, "ats_shortlisting/home.html", context)


@login_required
@admin_or_superuser_required
@hx_request_required
def ats_import_progress(request, run_id):
    progress = cache.get(_progress_key(run_id))
    if progress is None:
        return HttpResponse(
            f'<div class="text-sm text-red-600">{_("Import run expired or not found.")}</div>'
        )

    if not progress.get("done"):
        total = progress.get("total") or 0
        processed = progress.get("processed") or 0
        pct = round(processed / total * 100, 1) if total else 0.0
        context = {"run_id": run_id, "progress": progress, "pct": pct, **_dashboard_context(request)}
        return render(request, "ats_shortlisting/partials/_import_progress.html", context)

    report = {
        "total_files": progress.get("total_files", progress.get("total", 0)),
        "counts": progress.get("counts", {}),
        "outcomes": progress.get("outcomes", []),
        "drive_warnings": progress.get("drive_warnings", []),
        "domain": progress.get("domain", ""),
        "run_id": run_id,
    }
    context = {"form": JobDescriptionForm(), "report": report, **_dashboard_context(request)}
    return render(request, "ats_shortlisting/partials/_run_import_result.html", context)


@login_required
@admin_or_superuser_required
def ats_export_import_report(request, run_id):
    progress = cache.get(_progress_key(run_id)) or {}
    outcomes = progress.get("outcomes", [])

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Import Report"
    sheet.append(["File Name", "Status", "ATS Score", "Reason"])
    for outcome in outcomes:
        sheet.append([
            outcome.get("file_name", ""), outcome.get("status", ""),
            outcome.get("ats_score", ""), outcome.get("reason", ""),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ATS_Import_Report.xlsx"'
    workbook.save(response)
    return response


@login_required
@admin_or_superuser_required
@hx_request_required
def ats_dashboard_partial(request):
    return render(request, "ats_shortlisting/partials/_dashboard.html", _dashboard_context(request))


@login_required
@admin_or_superuser_required
def ats_export_candidates(request):
    candidates = _dashboard_context(request)["candidates"]

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Applicants"
    sheet.append([
        "Candidate ID", "Name", "Email", "Phone", "Experience", "Skills",
        "Detected Job Domain", "Education", "ATS Score", "Skill Match %",
        "Experience Match %", "Matched Skills", "Missing Skills",
        "Recommendation", "Status", "Resume File Name", "Imported Time",
    ])
    for candidate in candidates:
        recommendation_cell = candidate.recommendation
        if candidate.recommendation_text:
            recommendation_cell = f"{candidate.recommendation} - {candidate.recommendation_text}"
        sheet.append([
            candidate.candidate_code, candidate.name, candidate.email, candidate.phone,
            candidate.experience_text, candidate.skills, candidate.detected_job_domain,
            candidate.education, candidate.ats_score, candidate.skill_match_pct,
            candidate.experience_match_pct, candidate.matched_skills, candidate.missing_skills,
            recommendation_cell, candidate.status, candidate.resume_file_name,
            candidate.imported_time.strftime("%Y-%m-%d %H:%M:%S") if candidate.imported_time else "",
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ATS_Applicants.xlsx"'
    workbook.save(response)
    return response
