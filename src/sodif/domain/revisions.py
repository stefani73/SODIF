"""Signed revision contracts and pure document-chain invariants."""

from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import DocumentFormat, SignatureAlgorithm
from sodif.domain.errors import InvalidRevisionChain
from sodif.domain.models import DocumentEnvelope
from sodif.domain.types import Digest, Identifier

DetachedSignature = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_-]{86}$"),
]
EncodedPublicKey = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9_-]{43}$"),
]


class SignedRevisionMetadata(DomainModel):
    """Metadata bound to document bytes by a detached signature."""

    protocol: Literal["sodif.signed-revision/v1"] = "sodif.signed-revision/v1"
    document_id: Identifier
    revision_number: int = Field(ge=1)
    format: DocumentFormat
    content_digest: Digest
    previous_revision_digest: Digest | None = None
    signer_id: Identifier
    key_id: Identifier
    algorithm: SignatureAlgorithm
    signed_at: AwareDatetime

    @model_validator(mode="after")
    def predecessor_matches_revision_number(self) -> Self:
        if self.revision_number == 1 and self.previous_revision_digest is not None:
            raise ValueError("the first revision cannot declare a predecessor")
        if self.revision_number > 1 and self.previous_revision_digest is None:
            raise ValueError("a later revision must declare its predecessor")
        return self


class SignedRevision(DomainModel):
    metadata: SignedRevisionMetadata
    signature: DetachedSignature


class TrustedSignerKey(DomainModel):
    key_id: Identifier
    signer_id: Identifier
    algorithm: SignatureAlgorithm
    public_key: EncodedPublicKey
    active_from: AwareDatetime
    active_until: AwareDatetime | None = None
    revoked_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def lifecycle_is_ordered(self) -> Self:
        if self.active_until is not None and self.active_until <= self.active_from:
            raise ValueError("key active_until must be after active_from")
        if self.revoked_at is not None and self.revoked_at < self.active_from:
            raise ValueError("key revoked_at cannot precede active_from")
        return self


class RevisionRecord(DomainModel):
    document_id: Identifier
    revision_number: int = Field(ge=1)
    format: DocumentFormat
    revision_digest: Digest
    previous_revision_digest: Digest | None = None
    signature_digest: Digest
    signer_id: Identifier
    key_id: Identifier
    signed_at: AwareDatetime
    accepted_at: AwareDatetime


class RevisionAcceptance(DomainModel):
    envelope: DocumentEnvelope
    record: RevisionRecord
    duplicate: bool = False

    @model_validator(mode="after")
    def envelope_matches_record(self) -> Self:
        if self.envelope.document_id != self.record.document_id:
            raise ValueError("envelope and revision record document identifiers differ")
        if self.envelope.revision_digest != self.record.revision_digest:
            raise ValueError("envelope and revision record digests differ")
        return self


def validate_revision_append(
    history: tuple[RevisionRecord, ...],
    candidate: RevisionRecord,
) -> None:
    """Validate that candidate extends history exactly once and without a fork."""
    if not history:
        if candidate.revision_number != 1 or candidate.previous_revision_digest is not None:
            raise InvalidRevisionChain("document history must start with revision 1")
        return

    latest = history[-1]
    if candidate.document_id != latest.document_id:
        raise InvalidRevisionChain("revision document_id differs from its history")
    if candidate.format is not latest.format:
        raise InvalidRevisionChain("document format cannot change between revisions")
    if candidate.revision_number != latest.revision_number + 1:
        raise InvalidRevisionChain("revision number must increment by exactly one")
    if candidate.previous_revision_digest != latest.revision_digest:
        raise InvalidRevisionChain("revision does not reference the latest accepted digest")
    if candidate.revision_digest in {item.revision_digest for item in history}:
        raise InvalidRevisionChain("document content was already accepted in this history")
    if candidate.signed_at <= latest.signed_at:
        raise InvalidRevisionChain("revision signed_at must increase")
    if candidate.accepted_at <= latest.accepted_at:
        raise InvalidRevisionChain("revision accepted_at must increase")
