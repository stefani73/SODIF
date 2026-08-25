"""Public page renderers for the SODIF product experience."""

from sodif.ui.pages.archive import render_archive_module
from sodif.ui.pages.configuration import render_configuration
from sodif.ui.pages.control import render_control_center
from sodif.ui.pages.evidence import render_evidence_hub
from sodif.ui.pages.gateway import render_gateway_module
from sodif.ui.pages.ingestion import render_document_ingestion
from sodif.ui.pages.overview import render_overview
from sodif.ui.pages.product import render_product_explainer
from sodif.ui.pages.registry import render_document_registry
from sodif.ui.pages.security import render_security_module

__all__ = [
    "render_archive_module",
    "render_configuration",
    "render_control_center",
    "render_document_ingestion",
    "render_document_registry",
    "render_evidence_hub",
    "render_gateway_module",
    "render_overview",
    "render_product_explainer",
    "render_security_module",
]
