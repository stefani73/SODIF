"""Pure invariants for signed metadata and linear revision history."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from sodif.domain.enums import DocumentFormat, SignatureAlgorithm, SignatureStatus
from sodif.domain.errors import InvalidRevisionChain
from sodif.domain.models import DocumentEnvelope, PolicyReference, SignatureEvidence
from sodif.domain.revisions import (
    RevisionAcceptance,
    RevisionRecord,
    SignedRevisionMetadata,
    TrustedSignerKey,
    validate_revision_append,
)

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def record(
    number: int,
    character: str,
    previous: str | None,
    *,
    document_id: str = "doc-001",
) -> RevisionRecord:
    moment = NOW + timedelta(minutes=number)
    return RevisionRecord(
        document_id=document_id,
        revision_number=number,
        format=DocumentFormat.PDF,
        revision_digest=digest(character),
        previous_revision_digest=previous,
        signature_digest=digest("f"),
        signer_id="signer-01",
        key_id="key-01",
        signed_at=moment,
        accepted_at=moment,
    )


def test_signed_metadata_requires_an_exact_predecessor_shape() -> None:
    base = {
        "document_id": "doc-001",
        "format": DocumentFormat.PDF,
        "content_digest": digest("a"),
        "signer_id": "signer-01",
        "key_id": "key-01",
        "algorithm": SignatureAlgorithm.ED25519,
        "signed_at": NOW,
    }

    first = SignedRevisionMetadata.model_validate({**base, "revision_number": 1})
    second = SignedRevisionMetadata.model_validate(
        {
            **base,
            "revision_number": 2,
            "previous_revision_digest": digest("a"),
        }
    )

    assert first.protocol == "sodif.signed-revision/v1"
    assert second.previous_revision_digest == digest("a")
    with pytest.raises(ValidationError, match="cannot declare a predecessor"):
        SignedRevisionMetadata.model_validate(
            {
                **base,
                "revision_number": 1,
                "previous_revision_digest": digest("b"),
            }
        )
    with pytest.raises(ValidationError, match="must declare its predecessor"):
        SignedRevisionMetadata.model_validate({**base, "revision_number": 2})


def test_trusted_key_lifecycle_must_be_ordered() -> None:
    base = {
        "key_id": "key-01",
        "signer_id": "signer-01",
        "algorithm": SignatureAlgorithm.ED25519,
        "public_key": "A" * 43,
        "active_from": NOW,
    }

    with pytest.raises(ValidationError, match="active_until"):
        TrustedSignerKey.model_validate({**base, "active_until": NOW})
    with pytest.raises(ValidationError, match="revoked_at"):
        TrustedSignerKey.model_validate({**base, "revoked_at": NOW - timedelta(seconds=1)})


def test_revision_acceptance_requires_matching_envelope() -> None:
    accepted = record(1, "a", None)
    envelope = DocumentEnvelope(
        document_id="doc-001",
        format=DocumentFormat.PDF,
        revision_digest=digest("a"),
        signatures=(
            SignatureEvidence(
                signer_id="signer-01",
                status=SignatureStatus.VALID,
                covers_revision=True,
                validated_at=NOW,
                validator_id="validator-01",
                validator_version="v1",
            ),
        ),
        policy=PolicyReference(policy_id="policy-01", version="v1", digest=digest("c")),
        ingested_at=NOW,
    )

    assert RevisionAcceptance(envelope=envelope, record=accepted).record == accepted
    with pytest.raises(ValidationError, match="document identifiers differ"):
        RevisionAcceptance(
            envelope=envelope,
            record=record(1, "a", None, document_id="doc-002"),
        )
    with pytest.raises(ValidationError, match="digests differ"):
        RevisionAcceptance(envelope=envelope, record=record(1, "b", None))


def test_linear_revision_chain_accepts_only_the_latest_successor() -> None:
    first = record(1, "a", None)
    second = record(2, "b", digest("a"))

    validate_revision_append((), first)
    validate_revision_append((first,), second)

    invalid = (
        record(2, "b", None),
        record(3, "b", digest("a")),
        record(2, "b", digest("c")),
        record(2, "a", digest("a")),
        record(2, "b", digest("a"), document_id="doc-002"),
        second.model_copy(update={"format": "pdf-invalid"}),
        second.model_copy(update={"signed_at": first.signed_at}),
        second.model_copy(update={"accepted_at": first.accepted_at}),
    )
    with pytest.raises(InvalidRevisionChain, match="start with revision 1"):
        validate_revision_append((), invalid[0])
    for candidate in invalid[1:]:
        with pytest.raises(InvalidRevisionChain):
            validate_revision_append((first,), candidate)
