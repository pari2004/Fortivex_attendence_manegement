"""
Vercel build hook (see [tool.vercel.scripts] in pyproject.toml).

Runs after Vercel installs requirements.txt but before the function is
bundled. Strips build-time-only tooling and third-party test suites out
of site-packages to keep the function under Vercel's 225MB bundle limit.
"""

import shutil
from pathlib import Path

import botocore
import googleapiclient

# googleapiclient.__file__ is <site-packages>/googleapiclient/__init__.py,
# so its grandparent is site-packages itself.
site_packages = Path(googleapiclient.__file__).parent.parent


def remove(path: Path, label: str) -> None:
    if not path.exists():
        return
    size_mb = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / (1024 * 1024)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"vercel_build_hook: removed {label} ({size_mb:.1f} MB)")


# google-api-python-client ships a discovery_cache/documents/ folder with
# static API descriptions for every Google API (Gmail, Sheets, Drive,
# Calendar, YouTube, etc.) - about 97MB - even though this project only
# calls the Calendar (horilla_meet) and Drive (horilla_backup) APIs.
# Removing it is safe: googleapiclient.discovery.build() falls back to
# fetching the discovery doc it needs over HTTPS when the local cache is
# missing.
remove(
    site_packages / "googleapiclient" / "discovery_cache" / "documents",
    "googleapiclient discovery_cache/documents",
)

# botocore ships per-service API definitions (service-2.json, paginators,
# waiters, examples) for every AWS service it knows about - EC2, Lambda,
# RDS, SageMaker, etc. - about 80MB, even though this project only talks
# to S3. Removing the service directories we don't use is safe: boto3
# only loads the model for a service when a client/resource for it is
# constructed, and this app only ever constructs an s3 client (via
# django-storages' S3Boto3Storage).
botocore_data = Path(botocore.__file__).parent / "data"
for service_dir in botocore_data.iterdir():
    if service_dir.is_dir() and service_dir.name not in ("s3", "s3control"):
        remove(service_dir, f"botocore data/{service_dir.name}")

# pip/setuptools/pkg_resources/wheel are packaging/build tooling, not
# runtime dependencies. The install step that needs them has already run
# by the time this hook fires, and nothing in this app or its runtime
# dependencies imports pkg_resources (pytz and numpy only reference it in
# comments or behind a `try/except ImportError` fallback that's never
# reached). Together these are ~18MB of dead weight in the bundle.
for name in ("pip", "setuptools", "pkg_resources", "wheel"):
    remove(site_packages / name, name)

# Third-party test suites (pandas/tests, numpy/**/tests, etc.) are never
# imported at runtime but pandas and numpy alone carry ~50MB of them.
# Sort deepest-first so shutil.rmtree never trips over a path whose
# parent a prior iteration already deleted.
test_dirs = sorted(
    (p for p in site_packages.glob("**/tests") if p.is_dir()),
    key=lambda p: len(p.parts),
    reverse=True,
)
for path in test_dirs:
    remove(path, str(path.relative_to(site_packages)))

# Stale bytecode caches - always safe to drop, Python recompiles on import.
pycache_dirs = sorted(
    (p for p in site_packages.glob("**/__pycache__") if p.is_dir()),
    key=lambda p: len(p.parts),
    reverse=True,
)
for path in pycache_dirs:
    remove(path, str(path.relative_to(site_packages)))
