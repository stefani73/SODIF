"""Contracts for execution-bound semantic invariance evidence."""

from typing import Literal, Self

from pydantic import Field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import ParameterLocation, SemanticDataType, ViewKind
from sodif.domain.types import Digest, FieldName, Identifier, JsonScalar


class SemanticChallenge(DomainModel):
    protocol: Literal["sodif.semantic-challenge/v1"] = "sodif.semantic-challenge/v1"
    challenge_id: Identifier
    document_id: Identifier
    revision_digest: Digest
    policy_digest: Digest
    server_nonce_digest: Digest
    selected_profiles: tuple[Identifier, ...] = Field(min_length=3)
    challenge_digest: Digest

    @model_validator(mode="after")
    def profiles_are_unique(self) -> Self:
        if len(self.selected_profiles) != len(set(self.selected_profiles)):
            raise ValueError("semantic challenge profiles must be unique")
        return self


class FieldEvidenceReference(DomainModel):
    view_id: Identifier
    view_kind: ViewKind
    adapter_id: Identifier
    adapter_version: Identifier
    locator: str = Field(min_length=1, max_length=512)
    provenance_digest: Digest


class StableFieldCommitment(DomainModel):
    name: FieldName
    data_type: SemanticDataType
    value: JsonScalar
    critical: bool
    evidence: tuple[FieldEvidenceReference, ...] = Field(min_length=2)
    leaf_digest: Digest

    @model_validator(mode="after")
    def evidence_is_independent(self) -> Self:
        view_ids = [item.view_id for item in self.evidence]
        adapter_ids = [item.adapter_id for item in self.evidence]
        if len(view_ids) != len(set(view_ids)):
            raise ValueError("field evidence view identifiers must be unique")
        if len(adapter_ids) != len(set(adapter_ids)):
            raise ValueError("field evidence adapters must be independent")
        return self


class SemanticInvarianceProof(DomainModel):
    protocol: Literal["sodif.semantic-invariance-proof/v1"] = "sodif.semantic-invariance-proof/v1"
    proof_id: Identifier
    document_id: Identifier
    revision_digest: Digest
    schema_id: Identifier
    schema_version: Identifier
    policy_digest: Digest
    challenge: SemanticChallenge
    fields: tuple[StableFieldCommitment, ...] = Field(min_length=1)
    field_root: Digest

    @model_validator(mode="after")
    def proof_context_is_consistent(self) -> Self:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("semantic proof field names must be unique")
        if (
            self.challenge.document_id != self.document_id
            or self.challenge.revision_digest != self.revision_digest
            or self.challenge.policy_digest != self.policy_digest
        ):
            raise ValueError("semantic challenge differs from proof context")
        return self


class ExecutionFieldBinding(DomainModel):
    parameter_name: FieldName
    parameter_location: ParameterLocation
    field_name: FieldName
    value_digest: Digest
    field_leaf_digest: Digest


class ExecutionProofBundle(DomainModel):
    protocol: Literal["sodif.execution-proof/v1"] = "sodif.execution-proof/v1"
    invariance: SemanticInvarianceProof
    action_digest: Digest
    bindings: tuple[ExecutionFieldBinding, ...] = Field(min_length=1)
    binding_root: Digest

    @model_validator(mode="after")
    def bindings_are_unique(self) -> Self:
        parameter_keys = [
            (binding.parameter_location, binding.parameter_name) for binding in self.bindings
        ]
        if len(parameter_keys) != len(set(parameter_keys)):
            raise ValueError("execution proof parameters must be unique")
        return self
