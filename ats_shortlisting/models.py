"""
ats_shortlisting/models.py

Persistent storage for the ATS Resume Shortlisting Tool, replacing the
reference tool's Applicants.xlsx with real DB tables. One ATSJobDescription
row is recorded per "Run Import & Scoring" click (for history/traceability);
ATSCandidate is the single running candidate pool, upserted (matched by
resume hash -> email -> phone, same as the reference tool's excel_store)
across runs regardless of which job description scored them last.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from horilla.models import HorillaModel, upload_path

RECOMMENDATION_CHOICES = [
    ("Shortlist", _("Shortlist")),
    ("Maybe", _("Maybe")),
    ("Reject", _("Reject")),
]

STATUS_CHOICES = [
    ("New", _("New")),
]

EDUCATION_CHOICES = [
    ("", _("Not specified")),
    ("high school", _("High School")),
    ("diploma", _("Diploma")),
    ("bachelor's", _("Bachelor's")),
    ("master's", _("Master's")),
    ("phd", _("PhD")),
]


class ATSJobDescription(HorillaModel):
    """One row per "Run Import & Scoring" click -- the scoring criteria a
    batch of resumes was measured against."""

    raw_text = models.TextField(verbose_name=_("Job Description"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("Detected Title"))
    domain = models.CharField(max_length=100, blank=True, verbose_name=_("Detected Domain"))
    required_skills = models.TextField(blank=True, verbose_name=_("Required Skills"))
    preferred_skills = models.TextField(blank=True, verbose_name=_("Preferred Skills"))
    soft_skills = models.TextField(blank=True, verbose_name=_("Soft Skills"))
    min_experience_years = models.FloatField(default=0.0, verbose_name=_("Min Experience (years)"))
    preferred_experience_years = models.FloatField(
        default=0.0, verbose_name=_("Preferred Experience (years)")
    )
    education_requirement = models.CharField(
        max_length=50, blank=True, choices=EDUCATION_CHOICES, verbose_name=_("Education Requirement")
    )
    certifications_required = models.TextField(blank=True, verbose_name=_("Certifications Required"))
    keywords = models.TextField(blank=True, verbose_name=_("Keywords"))
    responsibilities = models.TextField(blank=True, verbose_name=_("Responsibilities"))

    weight_required_skills = models.FloatField(default=40.0)
    weight_preferred_skills = models.FloatField(default=20.0)
    weight_experience = models.FloatField(default=15.0)
    weight_education = models.FloatField(default=10.0)
    weight_certifications = models.FloatField(default=10.0)
    weight_resume_quality = models.FloatField(default=5.0)

    shortlist_threshold = models.FloatField(default=75.0)
    maybe_threshold = models.FloatField(default=50.0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("ATS Job Description")
        verbose_name_plural = _("ATS Job Descriptions")

    def __str__(self):
        return self.title or (self.raw_text[:50] if self.raw_text else f"JD #{self.pk}")

    def skill_list(self, field_name):
        value = getattr(self, field_name, "") or ""
        return [s.strip() for s in value.split(",") if s.strip()]


class ATSCandidate(HorillaModel):
    """The running candidate pool. Matched/upserted across import runs by
    resume hash, then email, then phone -- the same 3-tier precedence as the
    reference tool's excel_store.find_existing_candidate."""

    candidate_code = models.CharField(max_length=20, unique=True, blank=True, verbose_name=_("Candidate ID"))
    name = models.CharField(max_length=200, default="Unknown", verbose_name=_("Name"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_("Phone"))

    experience_text = models.CharField(max_length=255, blank=True, verbose_name=_("Experience"))
    total_experience_years = models.FloatField(default=0.0)

    skills = models.TextField(blank=True, verbose_name=_("Skills"))
    detected_job_domain = models.CharField(max_length=100, blank=True, verbose_name=_("Detected Job Domain"))
    education = models.TextField(blank=True, verbose_name=_("Education"))

    ats_score = models.FloatField(default=0.0, verbose_name=_("ATS Score"))
    skill_match_pct = models.FloatField(default=0.0, verbose_name=_("Skill Match %"))
    experience_match_pct = models.FloatField(default=0.0, verbose_name=_("Experience Match %"))
    matched_skills = models.TextField(blank=True, verbose_name=_("Matched Skills"))
    missing_skills = models.TextField(blank=True, verbose_name=_("Missing Skills"))

    recommendation = models.CharField(
        max_length=20, choices=RECOMMENDATION_CHOICES, default="Reject", verbose_name=_("Recommendation")
    )
    recommendation_text = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="New", verbose_name=_("Status"))

    resume = models.FileField(upload_to=upload_path, blank=True, null=True, verbose_name=_("Resume"))
    resume_file_name = models.CharField(max_length=255, blank=True, verbose_name=_("Resume File Name"))
    resume_hash = models.CharField(max_length=64, blank=True, db_index=True)

    google_drive_file_id = models.CharField(max_length=100, blank=True)
    google_drive_url = models.URLField(max_length=500, blank=True)

    last_job_description = models.ForeignKey(
        ATSJobDescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidates",
        verbose_name=_("Scored Against"),
    )
    imported_time = models.DateTimeField(auto_now=True, verbose_name=_("Imported Time"))

    class Meta:
        ordering = ["-ats_score", "name"]
        verbose_name = _("ATS Candidate")
        verbose_name_plural = _("ATS Candidates")

    def __str__(self):
        return f"{self.candidate_code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.candidate_code:
            last = ATSCandidate.objects.exclude(candidate_code="").order_by("-id").first()
            next_n = 1
            if last and last.candidate_code.upper().startswith("CAND-"):
                try:
                    next_n = int(last.candidate_code.split("-", 1)[1]) + 1
                except ValueError:
                    next_n = (last.id or 0) + 1
            self.candidate_code = f"CAND-{next_n:04d}"
        super().save(*args, **kwargs)

    @property
    def recommendation_tier(self):
        return self.recommendation
