"""Streamlit entry point for the document registry."""

from sodif.archive import build_local_registry_service
from sodif.settings import load_settings
from sodif.ui.pages.registry import render_document_registry

settings = load_settings()
render_document_registry(
    build_local_registry_service(settings.archive_root),
    "pages/ingestion.py",
)
