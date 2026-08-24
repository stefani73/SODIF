"""Binary-boundary tests for accepted document artifacts."""

from typing import cast

import pytest

from sodif.documents.content import DocumentContentPolicy, validate_document_content
from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.domain.enums import DocumentFormat

PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


def test_valid_pdf_returns_exact_binary_digest() -> None:
    result = validate_document_content(PDF, DocumentFormat.PDF, DocumentContentPolicy())

    assert result == "sha256:14fb1bb0a3f76503d164c7fd78a07c420c2f07eecd41793b406c6f75f2bc2aba"


@pytest.mark.parametrize(
    ("content", "policy", "code"),
    [
        (b"", DocumentContentPolicy(), DocumentRejectionCode.EMPTY_DOCUMENT),
        (b"not-a-pdf", DocumentContentPolicy(), DocumentRejectionCode.MALFORMED_PDF),
        (b"%PDF-1.7\nmissing-eof", DocumentContentPolicy(), DocumentRejectionCode.MALFORMED_PDF),
        (PDF, DocumentContentPolicy(max_bytes=5), DocumentRejectionCode.DOCUMENT_TOO_LARGE),
    ],
)
def test_binary_policy_rejects_invalid_documents(
    content: bytes,
    policy: DocumentContentPolicy,
    code: DocumentRejectionCode,
) -> None:
    with pytest.raises(DocumentRejected) as captured:
        validate_document_content(content, DocumentFormat.PDF, policy)

    assert captured.value.code is code


def test_binary_boundary_rejects_mutable_input_and_invalid_policy() -> None:
    with pytest.raises(DocumentRejected) as captured:
        validate_document_content(
            cast(bytes, bytearray(PDF)),
            DocumentFormat.PDF,
            DocumentContentPolicy(),
        )
    with pytest.raises(ValueError, match="positive"):
        DocumentContentPolicy(max_bytes=0)

    assert captured.value.code is DocumentRejectionCode.INVALID_BINARY_INPUT
