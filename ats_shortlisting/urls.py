"""
ats_shortlisting/urls.py
"""

from django.urls import path

from ats_shortlisting import views

urlpatterns = [
    path("", views.ats_home, name="ats-tool-home"),
    path("analyze-jd/", views.ats_analyze_jd, name="ats-tool-analyze-jd"),
    path("run-import/", views.ats_run_import, name="ats-tool-run-import"),
    path("import-progress/<str:run_id>/", views.ats_import_progress, name="ats-tool-import-progress"),
    path("import-report/<str:run_id>/export/", views.ats_export_import_report, name="ats-tool-export-import-report"),
    path("dashboard/", views.ats_dashboard_partial, name="ats-tool-dashboard"),
    path("export/", views.ats_export_candidates, name="ats-tool-export"),
]
