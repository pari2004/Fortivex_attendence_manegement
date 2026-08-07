"""
daily_report/forms.py
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms import ModelForm
from daily_report.models import DailyReport


class DailyReportForm(ModelForm):
    """
    Form used to create/update a DailyReport.
    """

    class Meta:
        model = DailyReport
        fields = ["report_date", "report"]
        widgets = {
            "report": forms.Textarea(
                attrs={"rows": 6, "placeholder": _("What did you work on today?")}
            ),
        }
