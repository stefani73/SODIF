"""Trusted deterministic signer profile used by the local demonstrator."""

from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sodif.documents.crypto import Ed25519RevisionSigner, encode_public_key
from sodif.domain.enums import DocumentFormat, SignatureAlgorithm
from sodif.domain.revisions import SignedRevision, SignedRevisionMetadata, TrustedSignerKey

DEMO_DOCUMENT_ID = "doc-flight-001"
DEMO_SIGNER_ID = "flight-signer"
DEMO_KEY_ID = "flight-document-key"
DEMO_SIGNED_AT = datetime(2026, 8, 24, 13, 59, tzinfo=UTC)


def demo_revision_signer() -> Ed25519RevisionSigner:
    """Return the stable local signer used to create inspectable sample evidence."""
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
    return Ed25519RevisionSigner(DEMO_SIGNER_ID, DEMO_KEY_ID, private_key)


def demo_trusted_signer() -> TrustedSignerKey:
    """Return the public trust entry corresponding to the local sample signer."""
    signer = demo_revision_signer()
    return TrustedSignerKey(
        key_id=signer.key_id,
        signer_id=signer.signer_id,
        algorithm=SignatureAlgorithm.ED25519,
        public_key=encode_public_key(signer.public_key()),
        active_from=DEMO_SIGNED_AT - timedelta(days=1),
    )


def sign_demo_revision(
    content: bytes,
    *,
    document_id: str = DEMO_DOCUMENT_ID,
    revision_number: int = 1,
    previous_revision_digest: str | None = None,
    signed_at: datetime = DEMO_SIGNED_AT,
) -> SignedRevision:
    """Sign one PDF revision with the local trusted demonstrator key."""
    from sodif.domain.canonical import sha256_bytes

    signer = demo_revision_signer()
    metadata = SignedRevisionMetadata(
        document_id=document_id,
        revision_number=revision_number,
        format=DocumentFormat.PDF,
        content_digest=sha256_bytes(content),
        previous_revision_digest=previous_revision_digest,
        signer_id=signer.signer_id,
        key_id=signer.key_id,
        algorithm=SignatureAlgorithm.ED25519,
        signed_at=signed_at,
    )
    return signer.sign(metadata)
