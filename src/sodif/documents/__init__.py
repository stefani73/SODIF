"""Signed-document boundary for the SODIF demonstrator."""

from sodif.documents.content import DocumentContentPolicy, validate_document_content
from sodif.documents.crypto import (
    Ed25519RevisionSigner,
    InMemoryTrustStore,
    encode_public_key,
    verify_revision_signature,
)
from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.documents.repository import InMemoryRevisionRepository, RevisionRepository
from sodif.documents.service import SignedRevisionService

__all__ = [
    "DocumentContentPolicy",
    "DocumentRejected",
    "DocumentRejectionCode",
    "Ed25519RevisionSigner",
    "InMemoryRevisionRepository",
    "InMemoryTrustStore",
    "RevisionRepository",
    "SignedRevisionService",
    "encode_public_key",
    "validate_document_content",
    "verify_revision_signature",
]
