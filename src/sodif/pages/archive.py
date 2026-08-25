"""Verifiable Document Archive module entry point."""

from sodif.ui.pages.archive import render_archive_module

render_archive_module("pages/ingestion.py", "pages/registry.py")
