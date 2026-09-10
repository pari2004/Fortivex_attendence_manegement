"""
ats_shortlisting/forms.py
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from ats_shortlisting.models import EDUCATION_CHOICES


class JobDescriptionForm(forms.Form):
    """Mirrors the reference tool's "1. Job Description" + weights +
    thresholds section. ``jd_text`` is the only field a user must fill in --
    everything else can be auto-detected via the Analyze step and then
    edited by hand."""

    jd_text = forms.CharField(
        label=_("Job Description"),
        widget=forms.Textarea(attrs={"rows": 8, "placeholder": _(
            "Paste any job description -- software, sales, HR, finance, healthcare, "
            "engineering, etc. Domain and required skills are detected automatically."
        )}),
    )
    required_skills = forms.CharField(
        label=_("Required skills (comma-separated)"), required=False,
        widget=forms.TextInput(attrs={"placeholder": "python, django, sql"}),
    )
    preferred_skills = forms.CharField(
        label=_("Preferred skills (comma-separated)"), required=False,
        widget=forms.TextInput(attrs={"placeholder": "docker, aws"}),
    )
    min_experience_years = forms.FloatField(
        label=_("Required years of experience"), required=False, min_value=0, max_value=40,
        initial=0,
    )
    preferred_experience_years = forms.FloatField(
        label=_("Preferred years of experience"), required=False, min_value=0, max_value=40,
        initial=0,
    )
    education_requirement = forms.ChoiceField(
        label=_("Education requirement"), required=False, choices=EDUCATION_CHOICES,
    )
    certifications_required = forms.CharField(
        label=_("Certifications required (comma-separated)"), required=False,
    )

    weight_required_skills = forms.IntegerField(label=_("Required skills %"), min_value=0, max_value=100, initial=40)
    weight_preferred_skills = forms.IntegerField(label=_("Preferred skills %"), min_value=0, max_value=100, initial=20)
    weight_experience = forms.IntegerField(label=_("Experience %"), min_value=0, max_value=100, initial=15)
    weight_education = forms.IntegerField(label=_("Education %"), min_value=0, max_value=100, initial=10)
    weight_certifications = forms.IntegerField(label=_("Certifications %"), min_value=0, max_value=100, initial=10)
    weight_resume_quality = forms.IntegerField(label=_("Resume quality %"), min_value=0, max_value=100, initial=5)

    shortlist_threshold = forms.IntegerField(label=_("Shortlist if ATS Score >="), min_value=0, max_value=100, initial=75)
    maybe_threshold = forms.IntegerField(label=_("Maybe if ATS Score >="), min_value=0, max_value=100, initial=50)

    drive_link = forms.CharField(
        label=_("Google Drive folder link"), required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://drive.google.com/drive/folders/..."}),
    )
    replace_existing = forms.BooleanField(
        label=_("Replace existing candidate database (deletes all current ATS candidates first)"),
        required=False, initial=True,
    )


class CandidateFilterForm(forms.Form):
    """Dashboard filters -- recommendation tier / minimum score / domain."""

    recommendation = forms.MultipleChoiceField(
        required=False,
        choices=[("Shortlist", _("Shortlist")), ("Maybe", _("Maybe")), ("Reject", _("Reject"))],
    )
    min_score = forms.IntegerField(required=False, min_value=0, max_value=100, initial=0)
    domain = forms.CharField(required=False)
    search = forms.CharField(required=False)
