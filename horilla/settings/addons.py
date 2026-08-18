"""
Optional integrations (e.g. AWS S3) layered on top of base settings.

Imported from horilla.settings.__init__ after base.py. Client overrides belong
in local_settings.py (imported after this module) — do not import them here.
"""

from .base import INSTALLED_APPS, env

if env("AWS_ACCESS_KEY_ID", default=None):
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default=None)
    DEFAULT_FILE_STORAGE = env(
        "DEFAULT_FILE_STORAGE",
        default="horilla.horilla_backends.PrivateMediaStorage",
    )
    AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", default="virtual")

    if "storages" not in INSTALLED_APPS:
        INSTALLED_APPS.append("storages")

# NOTE: MEDIA_ROOT/MEDIA_URL intentionally stay pointed at local disk (see
# base.py) even when S3 is enabled above. PrivateMediaStorage uses a private
# ACL with signed URLs, so it never reads Django's global MEDIA_URL/MEDIA_ROOT
# to build file URLs - and other code (e.g. horilla_views' PDF media-path
# resolution) assumes MEDIA_ROOT is a real local directory it can read from.
