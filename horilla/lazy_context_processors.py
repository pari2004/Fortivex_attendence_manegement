"""
horilla/lazy_context_processors.py

Deferred versions of the read-only template context processors.

Django runs every context processor on every template render with a request,
including small HTMX fragments that never read these variables, so each render
paid ~15 settings/company DB queries up front. The wrappers here expose the
same keys, but each value is a callable that runs the original processor on
first access and reuses that result for the rest of the render. Django's
template engine calls callables during variable resolution, so templates see
exactly the same values as before.

Only processors without side effects are wrapped. Processors that write rows,
change the session or mutate module state (breadcrumbs, sidebar menus,
biometric_is_installed, default_currency, enable_profile_edit) stay eager and
are still registered directly in settings.
"""

from base import context_processors as base_processors
from horilla_tour import context_processors as tour_processors


class _LazyContextValue:
    """Resolves one key of a shared, once-per-render processor result."""

    __slots__ = ("_loader", "_key")

    def __init__(self, loader, key):
        self._loader = loader
        self._key = key

    def __call__(self):
        return self._loader()[self._key]


def _deferred(processor, keys):
    def lazy_processor(request):
        result = {}

        def load():
            if not result:
                result.update(processor(request))
            return result

        return {key: _LazyContextValue(load, key) for key in keys}

    lazy_processor.__name__ = processor.__name__
    lazy_processor.__doc__ = processor.__doc__
    return lazy_processor


get_companies = _deferred(
    base_processors.get_companies,
    ("all_companies", "company_selected", "show_company_switcher"),
)
resignation_request_enabled = _deferred(
    base_processors.resignation_request_enabled, ("enabled_resignation_request",)
)
timerunner_enabled = _deferred(
    base_processors.timerunner_enabled, ("enabled_timerunner",)
)
intial_notice_period = _deferred(
    base_processors.intial_notice_period, ("get_initial_notice_period",)
)
check_candidate_self_tracking = _deferred(
    base_processors.check_candidate_self_tracking, ("check_candidate_self_tracking",)
)
check_candidate_self_tracking_rating = _deferred(
    base_processors.check_candidate_self_tracking_rating,
    ("check_candidate_self_tracking_rating",),
)
get_initial_prefix = _deferred(
    base_processors.get_initial_prefix, ("get_initial_prefix", "prefix_instance_id")
)
enable_late_come_early_out_tracking = _deferred(
    base_processors.enable_late_come_early_out_tracking,
    ("tracking", "late_come_early_out_tracking"),
)
export_access_enabled = _deferred(
    base_processors.export_access_enabled, ("export_access_enabled",)
)
navbar_languages = _deferred(
    base_processors.navbar_languages, ("navbar_languages", "show_language_switcher")
)
pending_tours_flag = _deferred(
    tour_processors.pending_tours_flag, ("tour_launcher_enabled", "tour_has_pending")
)
