"""Cryptographic binding and trust-policy tests for signed revisions."""

from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sodif.documents.crypto import (
    Ed25519RevisionSigner,
    InMemoryTrustStore,
    encode_public_key,
    verify_revision_signature,
)
from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.domain.enums import DocumentFormat, SignatureAlgorithm, SignatureStatus
from sodif.domain.revisions import SignedRevision, SignedRevisionMetadata, TrustedSignerKey

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
SIGNED_AT = NOW - timedelta(minutes=5)


def signer() -> Ed25519RevisionSigner:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
    return Ed25519RevisionSigner("signer-01", "key-01", private_key)


def metadata() -> SignedRevisionMetadata:
    return SignedRevisionMetadata(
        document_id="doc-001",
        revision_number=1,
        format=DocumentFormat.PDF,
        content_digest=f"sha256:{'a' * 64}",
        signer_id="signer-01",
        key_id="key-01",
        algorithm=SignatureAlgorithm.ED25519,
        signed_at=SIGNED_AT,
    )


def trusted_key(**updates: object) -> TrustedSignerKey:
    base: dict[str, object] = {
        "key_id": "key-01",
        "signer_id": "signer-01",
        "algorithm": SignatureAlgorithm.ED25519,
        "public_key": encode_public_key(signer().public_key()),
        "active_from": SIGNED_AT - timedelta(days=1),
    }
    return TrustedSignerKey.model_validate({**base, **updates})


def test_valid_signature_covers_canonical_revision_metadata() -> None:
    revision = signer().sign(metadata())

    evidence, signature_digest = verify_revision_signature(
        revision,
        InMemoryTrustStore((trusted_key(),)),
        NOW,
    )

    assert evidence.status is SignatureStatus.VALID
    assert evidence.covers_revision is True
    assert signature_digest.startswith("sha256:")


def test_metadata_change_and_unknown_key_are_rejected() -> None:
    signed = signer().sign(metadata())
    tampered = SignedRevision(
        metadata=signed.metadata.model_copy(update={"document_id": "doc-002"}),
        signature=signed.signature,
    )

    with pytest.raises(DocumentRejected) as changed:
        verify_revision_signature(tampered, InMemoryTrustStore((trusted_key(),)), NOW)
    with pytest.raises(DocumentRejected) as unknown:
        verify_revision_signature(signed, InMemoryTrustStore(()), NOW)

    assert changed.value.code is DocumentRejectionCode.SIGNATURE_INVALID
    assert unknown.value.code is DocumentRejectionCode.UNTRUSTED_KEY


@pytest.mark.parametrize(
    ("key_updates", "time", "code"),
    [
        ({"signer_id": "signer-02"}, NOW, DocumentRejectionCode.SIGNER_KEY_MISMATCH),
        (
            {"active_from": SIGNED_AT + timedelta(seconds=1)},
            NOW,
            DocumentRejectionCode.KEY_NOT_ACTIVE,
        ),
        ({"revoked_at": SIGNED_AT}, NOW, DocumentRejectionCode.KEY_REVOKED),
        ({}, SIGNED_AT - timedelta(seconds=1), DocumentRejectionCode.SIGNING_TIME_INVALID),
    ],
)
def test_trust_lifecycle_fails_closed(
    key_updates: dict[str, object],
    time: datetime,
    code: DocumentRejectionCode,
) -> None:
    revision = signer().sign(metadata())

    with pytest.raises(DocumentRejected) as captured:
        verify_revision_signature(
            revision,
            InMemoryTrustStore((trusted_key(**key_updates),)),
            time,
        )

    assert captured.value.code is code


def test_signer_and_trust_store_reject_ambiguous_configuration() -> None:
    with pytest.raises(ValueError, match="metadata"):
        signer().sign(metadata().model_copy(update={"signer_id": "signer-02"}))
    key = trusted_key()
    with pytest.raises(ValueError, match="unique"):
        InMemoryTrustStore((key, key))
