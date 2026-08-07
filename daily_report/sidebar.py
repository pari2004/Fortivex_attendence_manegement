"""
daily_report/sidebar.py
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

MENU = _("Daily Report")
IMG_SRC = "images/ui/report.svg"

SUBMENUS = [
    {
        "menu": _("My Reports"),
        "redirect": reverse_lazy("daily-report-view"),
    },
]
