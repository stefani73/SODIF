"""Cryptographic execution-permit contracts."""

from typing import Literal, Self

from pydantic import AwareDatetime, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import SignatureAlgorithm
from sodif.domain.revisions import DetachedSignature, EncodedPublicKey
from sodif.domain.types import Digest, Identifier


class ExecutionPermitClaims(DomainModel):
    protocol: Literal["sodif.execution-permit/v1"] = "sodif.execution-permit/v1"
    permit_id: Identifier
    issuer_id: Identifier
    key_id: Identifier
    algorithm: SignatureAlgorithm
    document_id: Identifier
    revision_digest: Digest
    verification_digest: Digest
    consensus_digest: Digest
    intent_digest: Digest
    action_digest: Digest
    policy_digest: Digest
    audience: Identifier
    issued_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def validity_window_is_positive(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("permit expires_at must be after issued_at")
        return self


class ExecutionPermit(DomainModel):
    claims: ExecutionPermitClaims
    signature: DetachedSignature


class TrustedPermitKey(DomainModel):
    key_id: Identifier
    issuer_id: Identifier
    algorithm: SignatureAlgorithm
    public_key: EncodedPublicKey
    active_from: AwareDatetime
    active_until: AwareDatetime | None = None
    revoked_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def lifecycle_is_ordered(self) -> Self:
        if self.active_until is not None and self.active_until <= self.active_from:
            raise ValueError("permit key active_until must be after active_from")
        if self.revoked_at is not None and self.revoked_at < self.active_from:
            raise ValueError("permit key revoked_at cannot precede active_from")
        return self


class PermitConsumption(DomainModel):
    permit_id: Identifier
    action_digest: Digest
    consumed_at: AwareDatetime


class ExecutionAuthorization(DomainModel):
    permit_id: Identifier
    document_id: Identifier
    revision_digest: Digest
    action_digest: Digest
    audience: Identifier
    authorized_at: AwareDatetime
    expires_at: AwareDatetime
