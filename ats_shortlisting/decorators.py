"""
ats_shortlisting/decorators.py

Access control for the ATS Resume Shortlisting Tool: Admin/HR Manager group
members and Django superusers only.
"""

from horilla.methods import handle_no_permission


def admin_or_superuser_required(function):
    """Allow only Django superusers or members of the "Admin"/"HR Manager" group."""

    def _function(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "HR Manager"]).exists()
        ):
            return function(request, *args, **kwargs)
        return handle_no_permission(request)

    return _function
