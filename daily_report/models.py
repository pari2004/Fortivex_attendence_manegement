"""
daily_report/models.py

Lets employees log a short note about what they worked on each day.
"""

from datetime import date

from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from base.horilla_company_manager import HorillaCompanyManager
from employee.models import Employee
from horilla.models import HorillaModel
from horilla_audit.models import HorillaAuditInfo, HorillaAuditLog


class DailyReport(HorillaModel):
    """
    One report per employee per day describing what they worked on.
    """

    employee_id = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="daily_reports",
        verbose_name=_("Employee"),
    )
    report_date = models.DateField(default=date.today, verbose_name=_("Date"))
    report = models.TextField(verbose_name=_("Daily Report"))

    objects = HorillaCompanyManager(
        related_company_field="employee_id__employee_work_info__company_id"
    )
    history = HorillaAuditLog(
        related_name="history_set",
        bases=[
            HorillaAuditInfo,
        ],
    )

    class Meta:
        """
        Meta class to add additional options
        """

        verbose_name = _("Daily Report")
        verbose_name_plural = _("Daily Reports")
        unique_together = ["employee_id", "report_date"]
        ordering = ["-report_date"]

    def __str__(self) -> str:
        return f"{self.employee_id} - {self.report_date}"

    def get_update_url(self):
        return reverse_lazy("daily-report-update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("daily-report-delete", kwargs={"pk": self.pk})
