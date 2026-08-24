"""End-to-end service tests for signed revision acceptance."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sodif.documents import (
    DocumentRejected,
    DocumentRejectionCode,
    Ed25519RevisionSigner,
    InMemoryRevisionRepository,
    InMemoryTrustStore,
    SignedRevisionService,
    encode_public_key,
)
from sodif.domain.canonical import sha256_bytes
from sodif.domain.contracts import SignedRevisionValidator
from sodif.domain.enums import DocumentFormat, SignatureAlgorithm, SignatureStatus
from sodif.domain.models import PolicyReference
from sodif.domain.revisions import SignedRevision, SignedRevisionMetadata, TrustedSignerKey

PDF_V1 = b"%PDF-1.7\n1 0 obj\n<</Revision 1>>\nendobj\n%%EOF\n"
PDF_V2 = b"%PDF-1.7\n1 0 obj\n<</Revision 2>>\nendobj\n%%EOF\n"
START = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


@dataclass
class MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


def build_signer() -> Ed25519RevisionSigner:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(33, 65)))
    return Ed25519RevisionSigner("signer-01", "key-01", private_key)


def build_service(
    clock: MutableClock,
) -> tuple[SignedRevisionService, InMemoryRevisionRepository, Ed25519RevisionSigner]:
    document_signer = build_signer()
    trusted = TrustedSignerKey(
        key_id="key-01",
        signer_id="signer-01",
        algorithm=SignatureAlgorithm.ED25519,
        public_key=encode_public_key(document_signer.public_key()),
        active_from=START - timedelta(days=1),
    )
    repository = InMemoryRevisionRepository()
    service = SignedRevisionService(InMemoryTrustStore((trusted,)), repository, clock)
    return service, repository, document_signer


def signed_revision(
    document_signer: Ed25519RevisionSigner,
    content: bytes,
    number: int,
    previous: str | None,
    signed_at: datetime,
) -> SignedRevision:
    metadata = SignedRevisionMetadata(
        document_id="doc-001",
        revision_number=number,
        format=DocumentFormat.PDF,
        content_digest=sha256_bytes(content),
        previous_revision_digest=previous,
        signer_id="signer-01",
        key_id="key-01",
        algorithm=SignatureAlgorithm.ED25519,
        signed_at=signed_at,
    )
    return document_signer.sign(metadata)


def policy() -> PolicyReference:
    return PolicyReference(
        policy_id="signed-document-policy",
        version="v1",
        digest=f"sha256:{'c' * 64}",
    )


def test_service_accepts_two_verified_linear_revisions() -> None:
    clock = MutableClock(START)
    service, repository, document_signer = build_service(clock)
    first = signed_revision(
        document_signer,
        PDF_V1,
        1,
        None,
        START - timedelta(minutes=2),
    )

    first_result = service.validate(PDF_V1, first, policy())
    clock.current = START + timedelta(minutes=2)
    second = signed_revision(
        document_signer,
        PDF_V2,
        2,
        first_result.record.revision_digest,
        START + timedelta(minutes=1),
    )
    second_result = service.validate(PDF_V2, second, policy())

    assert isinstance(service, SignedRevisionValidator)
    assert second_result.record.revision_number == 2
    assert second_result.envelope.signatures[0].status is SignatureStatus.VALID
    assert repository.history("doc-001") == (first_result.record, second_result.record)


def test_changed_bytes_are_rejected_before_acceptance() -> None:
    clock = MutableClock(START)
    service, repository, document_signer = build_service(clock)
    revision = signed_revision(
        document_signer,
        PDF_V1,
        1,
        None,
        START - timedelta(minutes=1),
    )

    with pytest.raises(DocumentRejected) as captured:
        service.validate(PDF_V2, revision, policy())

    assert captured.value.code is DocumentRejectionCode.CONTENT_DIGEST_MISMATCH
    assert repository.history("doc-001") == ()


@pytest.mark.parametrize(("number", "content"), [(3, PDF_V2), (2, PDF_V1)])
def test_invalid_sequence_and_content_reuse_are_rejected(
    number: int,
    content: bytes,
) -> None:
    clock = MutableClock(START)
    service, repository, document_signer = build_service(clock)
    first = signed_revision(
        document_signer,
        PDF_V1,
        1,
        None,
        START - timedelta(minutes=2),
    )
    accepted = service.validate(PDF_V1, first, policy())
    clock.current = START + timedelta(minutes=2)
    invalid = signed_revision(
        document_signer,
        content,
        number,
        accepted.record.revision_digest,
        START + timedelta(minutes=1),
    )

    with pytest.raises(DocumentRejected) as captured:
        service.validate(content, invalid, policy())

    assert captured.value.code is DocumentRejectionCode.REVISION_CHAIN_INVALID
    assert len(repository.history("doc-001")) == 1
