"""
daily_report/apps.py
"""

from django.apps import AppConfig


class DailyReportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "daily_report"

    def ready(self):
        from django.conf import settings
        from django.urls import include, path

        from horilla.urls import urlpatterns

        settings.APPS.append("daily_report")
        urlpatterns.append(
            path("daily-report/", include("daily_report.urls")),
        )
        settings.APP_URLS.append("daily_report.urls")

        super().ready()
