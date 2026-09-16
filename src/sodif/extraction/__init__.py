"""Real PDF structural and visual extraction adapters."""

from sodif.extraction.pdf import (
    PopplerTesseractAdapter,
    PyMuPDFTesseractAdapter,
    PyPdfStructuralAdapter,
    VisualExtractionProfile,
    challenged_pdf_adapters,
)

__all__ = [
    "PopplerTesseractAdapter",
    "PyMuPDFTesseractAdapter",
    "PyPdfStructuralAdapter",
    "VisualExtractionProfile",
    "challenged_pdf_adapters",
]
