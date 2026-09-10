"""
ats_shortlisting/apps.py
"""

from django.apps import AppConfig


class AtsShortlistingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ats_shortlisting"
    verbose_name = "ATS Resume Shortlisting Tool"

    def ready(self):
        from django.conf import settings
        from django.urls import include, path

        from horilla.urls import urlpatterns

        settings.APPS.append("ats_shortlisting")
        urlpatterns.append(
            path("ats-tool/", include("ats_shortlisting.urls")),
        )
        settings.APP_URLS.append("ats_shortlisting.urls")

        super().ready()
