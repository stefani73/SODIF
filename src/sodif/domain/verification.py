"""Immutable evidence produced by adaptive semantic verification."""

from typing import Self

from pydantic import Field, computed_field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import (
    ConsensusStatus,
    VerificationLevel,
    VerificationOutcomeStatus,
)
from sodif.domain.models import ConsensusResult, RiskAssessment, SemanticView
from sodif.domain.types import Digest, Identifier


class VerificationAttempt(DomainModel):
    level: VerificationLevel
    adapters_added: tuple[Identifier, ...] = Field(min_length=1)
    view_ids_evaluated: tuple[Identifier, ...] = Field(min_length=2)
    incremental_cost_units: int = Field(ge=1)
    consensus: ConsensusResult

    @model_validator(mode="after")
    def identifiers_are_unique(self) -> Self:
        if len(self.adapters_added) != len(set(self.adapters_added)):
            raise ValueError("attempt adapter identifiers must be unique")
        if len(self.view_ids_evaluated) != len(set(self.view_ids_evaluated)):
            raise ValueError("attempt view identifiers must be unique")
        return self


class AdaptiveVerificationOutcome(DomainModel):
    document_id: Identifier
    revision_digest: Digest
    status: VerificationOutcomeStatus
    initial_level: VerificationLevel
    final_level: VerificationLevel
    risk: RiskAssessment
    views: tuple[SemanticView, ...] = ()
    attempts: tuple[VerificationAttempt, ...] = ()
    final_consensus: ConsensusResult | None = None
    total_cost_units: int = Field(ge=0)
    available_cost_units: int = Field(ge=0)
    reasons: tuple[Identifier, ...] = Field(min_length=1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def saved_cost_units(self) -> int:
        return self.available_cost_units - self.total_cost_units

    @model_validator(mode="after")
    def outcome_is_internally_consistent(self) -> Self:
        if self.total_cost_units > self.available_cost_units:
            raise ValueError("verification cost exceeds the available route")
        if self.total_cost_units != sum(item.incremental_cost_units for item in self.attempts):
            raise ValueError("verification cost must equal attempt costs")
        if len({view.view_id for view in self.views}) != len(self.views):
            raise ValueError("outcome view identifiers must be unique")
        if self.status is VerificationOutcomeStatus.BLOCKED:
            if self.initial_level is not VerificationLevel.V0_BLOCK:
                raise ValueError("blocked outcome requires V0_BLOCK")
            if self.views or self.attempts or self.final_consensus is not None:
                raise ValueError("blocked outcome cannot contain semantic execution")
        else:
            if not self.attempts or self.final_consensus is None:
                raise ValueError("non-blocked outcome requires semantic attempts and consensus")
            if self.final_consensus.document_id != self.document_id:
                raise ValueError("final consensus document_id differs from outcome")
            if self.final_consensus.revision_digest != self.revision_digest:
                raise ValueError("final consensus revision differs from outcome")
        if self.status is VerificationOutcomeStatus.ACCEPTED and (
            self.final_consensus is None
            or self.final_consensus.status is not ConsensusStatus.ACCEPTED
            or self.final_level is VerificationLevel.V3_REVIEW
        ):
            raise ValueError("accepted outcome requires automated accepted consensus")
        return self
