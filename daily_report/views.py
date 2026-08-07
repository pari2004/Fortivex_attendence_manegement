"""
daily_report/views.py
"""

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from daily_report.forms import DailyReportForm
from daily_report.models import DailyReport
from horilla.decorators import hx_request_required, login_required
from horilla.http.response import HorillaRedirect


def _visible_reports(request):
    """
    Employees can only see their own daily reports unless they have the
    view-all permission or are a reporting manager (who can then see
    their direct reports' entries too).
    """
    employee = request.user.employee_get
    if request.user.has_perm("daily_report.view_dailyreport"):
        reports = DailyReport.objects.all()
    else:
        reports = DailyReport.objects.filter(
            Q(employee_id=employee)
            | Q(employee_id__employee_work_info__reporting_manager_id=employee)
        )

    can_manage_all = request.user.has_perm(
        "daily_report.change_dailyreport"
    ) or request.user.has_perm("daily_report.delete_dailyreport")
    for report in reports:
        report.can_edit = can_manage_all or report.employee_id == employee
    return reports


@login_required
def daily_report_view(request):
    """
    Main daily reports page.
    """
    reports = _visible_reports(request)
    show_employee_column = reports.count() != reports.filter(
        employee_id=request.user.employee_get
    ).count()
    return render(
        request,
        "daily_report/report_list.html",
        {"reports": reports, "show_employee_column": show_employee_column},
    )


@login_required
@hx_request_required
def daily_report_table(request):
    """
    htmx partial — re-renders just the reports table.
    """
    reports = _visible_reports(request)
    show_employee_column = reports.count() != reports.filter(
        employee_id=request.user.employee_get
    ).count()
    return render(
        request,
        "daily_report/report_table.html",
        {"reports": reports, "show_employee_column": show_employee_column},
    )


@login_required
@hx_request_required
def daily_report_create(request):
    """
    Create today's (or a chosen date's) daily report for the logged-in employee.
    """
    employee = request.user.employee_get
    form = DailyReportForm()
    if request.method == "POST":
        form = DailyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.employee_id = employee
            try:
                with transaction.atomic():
                    report.save()
            except IntegrityError:
                form.add_error(
                    "report_date",
                    _("A report for this date already exists — edit it instead."),
                )
            else:
                messages.success(request, _("Daily report saved."))
                return HorillaRedirect(request)
    return render(request, "daily_report/form.html", {"form": form})


@login_required
@hx_request_required
def daily_report_update(request, pk):
    """
    Update an existing daily report. Only the owner, or a user with the
    change permission, may edit it.
    """
    report = get_object_or_404(DailyReport, pk=pk)
    employee = request.user.employee_get
    if report.employee_id != employee and not request.user.has_perm(
        "daily_report.change_dailyreport"
    ):
        messages.error(request, _("You don't have permission to edit this report."))
        return HorillaRedirect(request)

    form = DailyReportForm(instance=report)
    if request.method == "POST":
        form = DailyReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, _("Daily report updated."))
            return HorillaRedirect(request)
    return render(request, "daily_report/form.html", {"form": form})


@login_required
@hx_request_required
def daily_report_delete(request, pk):
    """
    Delete a daily report. Only the owner, or a user with the delete
    permission, may delete it.
    """
    report = get_object_or_404(DailyReport, pk=pk)
    employee = request.user.employee_get
    if report.employee_id != employee and not request.user.has_perm(
        "daily_report.delete_dailyreport"
    ):
        messages.error(request, _("You don't have permission to delete this report."))
        return HorillaRedirect(request)

    report.delete()
    messages.success(request, _("Daily report deleted."))
    reports = _visible_reports(request)
    show_employee_column = reports.count() != reports.filter(
        employee_id=employee
    ).count()
    return render(
        request,
        "daily_report/report_table.html",
        {"reports": reports, "show_employee_column": show_employee_column},
    )
