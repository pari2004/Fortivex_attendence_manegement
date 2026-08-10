"""
Vercel build hook (see [tool.vercel.scripts] in pyproject.toml).

Runs after Vercel installs requirements.txt but before the function is
bundled. google-api-python-client ships a discovery_cache/documents/
folder with static API descriptions for every Google API (Gmail, Sheets,
Drive, Calendar, YouTube, etc.) - about 97MB - even though this project
only calls the Calendar (horilla_meet) and Drive (horilla_backup) APIs.
Removing it is safe: googleapiclient.discovery.build() falls back to
fetching the discovery doc it needs over HTTPS when the local cache is
missing.
"""

import shutil
from pathlib import Path

import googleapiclient

cache_dir = Path(googleapiclient.__file__).parent / "discovery_cache" / "documents"

if cache_dir.exists():
    size_mb = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file()) / (1024 * 1024)
    shutil.rmtree(cache_dir)
    print(f"vercel_build_hook: removed {cache_dir} ({size_mb:.1f} MB)")
else:
    print("vercel_build_hook: discovery_cache/documents not found, nothing to remove")
