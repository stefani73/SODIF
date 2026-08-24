"""Minimal binary policy for documents accepted by the TRL 4 demonstrator."""

import re
from dataclasses import dataclass

from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.domain.canonical import sha256_bytes
from sodif.domain.enums import DocumentFormat
from sodif.domain.types import Digest

_PDF_HEADER = re.compile(rb"^%PDF-(?:1\.[0-7]|2\.0)(?:\r\n|\r|\n)")


@dataclass(frozen=True, slots=True)
class DocumentContentPolicy:
    max_bytes: int = 10 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be positive")


def validate_document_content(
    content: bytes,
    document_format: DocumentFormat,
    policy: DocumentContentPolicy,
) -> Digest:
    """Validate the binary boundary and return the exact accepted digest."""
    if not isinstance(content, bytes):
        raise DocumentRejected(
            DocumentRejectionCode.INVALID_BINARY_INPUT,
            "document content must be immutable bytes",
        )
    if not content:
        raise DocumentRejected(DocumentRejectionCode.EMPTY_DOCUMENT, "document is empty")
    if len(content) > policy.max_bytes:
        raise DocumentRejected(
            DocumentRejectionCode.DOCUMENT_TOO_LARGE,
            f"document exceeds the {policy.max_bytes}-byte policy limit",
        )
    if document_format is DocumentFormat.PDF and (
        _PDF_HEADER.match(content) is None or not content.rstrip().endswith(b"%%EOF")
    ):
        raise DocumentRejected(
            DocumentRejectionCode.MALFORMED_PDF,
            "PDF header or terminal marker is invalid",
        )
    return sha256_bytes(content)
