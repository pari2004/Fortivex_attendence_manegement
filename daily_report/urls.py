"""
daily_report/urls.py
"""

from django.urls import path

from daily_report import views

urlpatterns = [
    path("", views.daily_report_view, name="daily-report-view"),
    path("table/", views.daily_report_table, name="daily-report-table"),
    path("create/", views.daily_report_create, name="daily-report-create"),
    path("<int:pk>/update/", views.daily_report_update, name="daily-report-update"),
    path("<int:pk>/delete/", views.daily_report_delete, name="daily-report-delete"),
]
