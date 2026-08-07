"""
Vercel serverless entrypoint.

Vercel's Python runtime (@vercel/python) looks for a WSGI-compatible
callable named ``app`` in this file. It reuses the project's real WSGI
config (horilla/wsgi.py) rather than duplicating it.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")

from horilla.wsgi import application as app
