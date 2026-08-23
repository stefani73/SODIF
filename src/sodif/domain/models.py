"""Immutable contracts exchanged by SODIF components."""

from decimal import Decimal
from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import (
    ConsensusStatus,
    DocumentFormat,
    HttpMethod,
    ParameterLocation,
    RiskSeverity,
    SemanticDataType,
    SignatureStatus,
    VerificationLevel,
    ViewKind,
)
from sodif.domain.types import Confidence, Digest, FieldName, Identifier, JsonScalar, RiskScore


class Attribute(DomainModel):
    key: Identifier
    value: str


class PolicyReference(DomainModel):
    policy_id: Identifier
    version: Identifier
    digest: Digest


class SignatureEvidence(DomainModel):
    signer_id: Identifier
    status: SignatureStatus
    covers_revision: bool
    validated_at: AwareDatetime
    validator_id: Identifier
    validator_version: Identifier


class DocumentEnvelope(DomainModel):
    document_id: Identifier
    format: DocumentFormat
    revision_digest: Digest
    signatures: tuple[SignatureEvidence, ...] = Field(min_length=1)
    policy: PolicyReference
    ingested_at: AwareDatetime
    attributes: tuple[Attribute, ...] = ()

    @model_validator(mode="after")
    def unique_signers_and_attributes(self) -> Self:
        signer_ids = [signature.signer_id for signature in self.signatures]
        attribute_keys = [attribute.key.casefold() for attribute in self.attributes]
        if len(signer_ids) != len(set(signer_ids)):
            raise ValueError("signature signer_id values must be unique")
        if len(attribute_keys) != len(set(attribute_keys)):
            raise ValueError("document attribute keys must be unique")
        return self


class FieldProvenance(DomainModel):
    view_kind: ViewKind
    adapter_id: Identifier
    adapter_version: Identifier
    locator: str = Field(min_length=1, max_length=512)
    source_digest: Digest


class SemanticField(DomainModel):
    name: FieldName
    data_type: SemanticDataType
    value: JsonScalar
    raw_value: str | None = None
    confidence: Confidence
    provenance: FieldProvenance


class SemanticView(DomainModel):
    view_id: Identifier
    document_id: Identifier
    revision_digest: Digest
    adapter_id: Identifier
    adapter_version: Identifier
    fields: tuple[SemanticField, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_field_names(self) -> Self:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("semantic field names must be unique inside a view")
        return self


class CandidateValue(DomainModel):
    view_id: Identifier
    value: JsonScalar
    confidence: Confidence
    provenance_digest: Digest


class ConsensusField(DomainModel):
    name: FieldName
    data_type: SemanticDataType
    status: ConsensusStatus
    accepted_value: JsonScalar = None
    candidates: tuple[CandidateValue, ...] = ()
    supporting_views: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def status_matches_evidence(self) -> Self:
        if self.status is ConsensusStatus.ACCEPTED:
            if self.accepted_value is None or not self.supporting_views:
                raise ValueError("accepted consensus requires a value and supporting views")
        elif self.accepted_value is not None:
            raise ValueError("non-accepted consensus cannot expose an accepted value")

        if self.status is ConsensusStatus.CONFLICT and len(self.candidates) < 2:
            raise ValueError("conflict consensus requires at least two candidates")
        if self.status is ConsensusStatus.MISSING and self.candidates:
            raise ValueError("missing consensus cannot contain candidates")
        if len(self.supporting_views) != len(set(self.supporting_views)):
            raise ValueError("supporting view identifiers must be unique")
        return self


class ConsensusResult(DomainModel):
    document_id: Identifier
    revision_digest: Digest
    status: ConsensusStatus
    fields: tuple[ConsensusField, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def global_status_matches_fields(self) -> Self:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("consensus field names must be unique")
        expected = ConsensusStatus.ACCEPTED
        if any(field.status is ConsensusStatus.CONFLICT for field in self.fields):
            expected = ConsensusStatus.CONFLICT
        elif any(field.status is ConsensusStatus.MISSING for field in self.fields):
            expected = ConsensusStatus.MISSING
        if self.status is not expected:
            raise ValueError(f"global consensus must be {expected.value}")
        return self


class IntentValue(DomainModel):
    name: FieldName
    data_type: SemanticDataType
    value: JsonScalar
    source_views: tuple[Identifier, ...] = Field(min_length=1)
    provenance_digests: tuple[Digest, ...] = Field(min_length=1)


class IntentManifest(DomainModel):
    manifest_id: Identifier
    document_id: Identifier
    revision_digest: Digest
    schema_id: Identifier
    schema_version: Identifier
    action_type: Identifier
    policy: PolicyReference
    fields: tuple[IntentValue, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_fields(self) -> Self:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("intent field names must be unique")
        return self


class ActionParameter(DomainModel):
    name: FieldName
    location: ParameterLocation
    value: JsonScalar


class ExecutionPlan(DomainModel):
    plan_id: Identifier
    intent_digest: Digest
    method: HttpMethod
    path: str = Field(pattern=r"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]+$")
    audience: Identifier
    parameters: tuple[ActionParameter, ...] = Field(min_length=1)
    headers: tuple[Attribute, ...] = ()

    @model_validator(mode="after")
    def unique_request_components(self) -> Self:
        parameter_keys = [(item.location, item.name) for item in self.parameters]
        header_keys = [header.key.casefold() for header in self.headers]
        if len(parameter_keys) != len(set(parameter_keys)):
            raise ValueError("action parameters must be unique by location and name")
        if len(header_keys) != len(set(header_keys)):
            raise ValueError("action headers must be unique")
        return self


class ActionContext(DomainModel):
    action_type: Identifier
    method: HttpMethod
    path: str = Field(pattern=r"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]+$")
    audience: Identifier


class RiskSignal(DomainModel):
    code: Identifier
    severity: RiskSeverity
    detail: str = Field(min_length=1, max_length=500)


class RiskAssessment(DomainModel):
    score: RiskScore
    verification_level: VerificationLevel
    policy: PolicyReference
    signals: tuple[RiskSignal, ...] = ()

    @model_validator(mode="after")
    def unique_signal_codes(self) -> Self:
        codes = [signal.code for signal in self.signals]
        if len(codes) != len(set(codes)):
            raise ValueError("risk signal codes must be unique")
        return self


class EvidenceEvent(DomainModel):
    event_id: Identifier
    correlation_id: Identifier
    event_type: Identifier
    occurred_at: AwareDatetime
    subject_digest: Digest
    attributes: tuple[Attribute, ...] = ()

    @model_validator(mode="after")
    def unique_attribute_keys(self) -> Self:
        keys = [attribute.key.casefold() for attribute in self.attributes]
        if len(keys) != len(set(keys)):
            raise ValueError("evidence attribute keys must be unique")
        return self


def percentage(value: str) -> Decimal:
    """Create an exact decimal for tests, policies and fixtures."""
    return Decimal(value)

