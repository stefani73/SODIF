"""Signed-document boundary for the SODIF demonstrator."""

from sodif.documents.content import DocumentContentPolicy, validate_document_content
from sodif.documents.crypto import (
    Ed25519RevisionSigner,
    InMemoryTrustStore,
    encode_public_key,
    verify_revision_signature,
)
from sodif.documents.demo import (
    DEMO_DOCUMENT_ID,
    demo_revision_signer,
    demo_trusted_signer,
    sign_demo_revision,
)
from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.documents.repository import InMemoryRevisionRepository, RevisionRepository
from sodif.documents.service import SignedRevisionService

__all__ = [
    "DEMO_DOCUMENT_ID",
    "DocumentContentPolicy",
    "DocumentRejected",
    "DocumentRejectionCode",
    "Ed25519RevisionSigner",
    "InMemoryRevisionRepository",
    "InMemoryTrustStore",
    "RevisionRepository",
    "SignedRevisionService",
    "demo_revision_signer",
    "demo_trusted_signer",
    "encode_public_key",
    "sign_demo_revision",
    "validate_document_content",
    "verify_revision_signature",
]
