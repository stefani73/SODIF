"""Stable rejection codes for signed-document processing."""

from enum import StrEnum


class DocumentRejectionCode(StrEnum):
    INVALID_BINARY_INPUT = "invalid_binary_input"
    EMPTY_DOCUMENT = "empty_document"
    DOCUMENT_TOO_LARGE = "document_too_large"
    MALFORMED_PDF = "malformed_pdf"
    CONTENT_DIGEST_MISMATCH = "content_digest_mismatch"
    UNTRUSTED_KEY = "untrusted_key"
    SIGNER_KEY_MISMATCH = "signer_key_mismatch"
    KEY_NOT_ACTIVE = "key_not_active"
    KEY_REVOKED = "key_revoked"
    SIGNING_TIME_INVALID = "signing_time_invalid"
    SIGNATURE_INVALID = "signature_invalid"
    REVISION_CHAIN_INVALID = "revision_chain_invalid"


class DocumentRejected(ValueError):
    """Expected, fail-closed outcome carrying a machine-readable reason."""

    def __init__(self, code: DocumentRejectionCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")
