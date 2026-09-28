"""
horilla/lazy_imports.py

Defers importing heavy third-party modules until they are first used.

pandas, xhtml2pdf and PyMuPDF (fitz) are only needed by import/export and PDF
views, but importing them at module level added ~400ms to every process start
(and so to every serverless cold start). ``LazyModule`` stands in for the
module object and performs the real import on first attribute access, so call
sites such as ``pd.DataFrame(...)`` or ``pisa.CreatePDF(...)`` are unchanged.
"""

import importlib


class LazyModule:
    """Module proxy that imports ``name`` on first attribute access."""

    def __init__(self, name):
        self._name = name
        self._module = None

    def _load(self):
        if self._module is None:
            self._module = importlib.import_module(self._name)
        return self._module

    def __getattr__(self, attr):
        return getattr(self._load(), attr)

    def __repr__(self):
        return f"<LazyModule {self._name!r}>"
