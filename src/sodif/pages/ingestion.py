"""Streamlit entry point for signed-document ingestion."""

from sodif.archive import build_local_ingestion_service
from sodif.settings import load_settings
from sodif.ui.pages.ingestion import render_document_ingestion

settings = load_settings()
render_document_ingestion(build_local_ingestion_service(settings.archive_root))
