"""Serializable flight-demo evidence."""

from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import ProcessingStage
from sodif.domain.execution import ExecutionReceipt
from sodif.domain.gateway import GatewayDecision, GatewayDecisionStatus
from sodif.domain.state import WorkflowState
from sodif.domain.types import Digest, Identifier
from sodif.domain.verification import AdaptiveVerificationOutcome


class FlightScenario(StrEnum):
    HAPPY_PATH = "happy-path"
    ADAPTIVE_RECOVERY = "adaptive-recovery"
    TAMPERED_DOCUMENT = "tampered-document"
    SEMANTIC_CONFLICT = "semantic-conflict"
    ACTION_TAMPERING = "action-tampering"
    REPLAY_ATTACK = "replay-attack"


class FlightKind(StrEnum):
    """Product-level scope of a reproducible demonstration flight."""

    SECURITY = "security"
    TRANSVERSAL = "transversal"


class ScenarioOutcome(StrEnum):
    EXECUTED = "executed"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


class ScenarioObservation(DomainModel):
    sequence: int = Field(ge=1)
    stage: Identifier
    detail: str = Field(min_length=1, max_length=500)
    occurred_at: AwareDatetime
    subject_digest: Digest | None = None


class ScenarioResult(DomainModel):
    scenario_id: FlightScenario
    title: str = Field(min_length=1, max_length=120)
    expected_outcome: ScenarioOutcome
    observed_outcome: ScenarioOutcome
    passed: bool
    workflow: WorkflowState
    observations: tuple[ScenarioObservation, ...] = Field(min_length=1)
    verification: AdaptiveVerificationOutcome | None = None
    archive_id: Identifier | None = None
    archive_ids: tuple[Identifier, ...] = ()
    permit_id: Identifier | None = None
    gateway_decisions: tuple[GatewayDecision, ...] = ()
    receipt: ExecutionReceipt | None = None
    rejection_code: Identifier | None = None

    @model_validator(mode="after")
    def terminal_evidence_matches_outcome(self) -> Self:
        if self.passed != (self.expected_outcome is self.observed_outcome):
            raise ValueError("scenario passed flag differs from expected and observed outcomes")
        expected_stage = {
            ScenarioOutcome.EXECUTED: ProcessingStage.EXECUTED,
            ScenarioOutcome.BLOCKED: ProcessingStage.BLOCKED,
            ScenarioOutcome.ESCALATED: ProcessingStage.ESCALATED,
        }[self.observed_outcome]
        if self.workflow.stage is not expected_stage:
            raise ValueError("workflow terminal stage differs from observed outcome")
        sequences = [item.sequence for item in self.observations]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("scenario observations must use contiguous sequence numbers")
        if self.observed_outcome is ScenarioOutcome.EXECUTED and self.receipt is None:
            raise ValueError("executed scenario requires an execution receipt")
        if self.observed_outcome is not ScenarioOutcome.EXECUTED and self.receipt is not None:
            raise ValueError("non-executed scenario cannot contain an execution receipt")
        if len(self.archive_ids) != len(set(self.archive_ids)):
            raise ValueError("scenario archive identifiers must be unique")
        if self.archive_ids and self.archive_id != self.archive_ids[-1]:
            raise ValueError("scenario archive_id must identify the latest archived revision")
        if not self.archive_ids and self.archive_id is not None:
            raise ValueError("scenario archive_id requires archive_ids evidence")
        decision_ids = [decision.decision_id for decision in self.gateway_decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("scenario gateway decision identifiers must be unique")
        if self.gateway_decisions:
            if self.permit_id is None:
                raise ValueError("gateway decisions require permit evidence")
            if any(decision.permit_id != self.permit_id for decision in self.gateway_decisions):
                raise ValueError("gateway decisions must reference the scenario permit")
            final_decision = self.gateway_decisions[-1]
            expected_gateway_status = {
                ScenarioOutcome.EXECUTED: GatewayDecisionStatus.ROUTED,
                ScenarioOutcome.BLOCKED: GatewayDecisionStatus.BLOCKED,
                ScenarioOutcome.ESCALATED: None,
            }[self.observed_outcome]
            if final_decision.status is not expected_gateway_status:
                raise ValueError("final gateway decision differs from the scenario outcome")
            if self.receipt is not None and final_decision.receipt != self.receipt:
                raise ValueError("gateway and scenario execution receipts must match")
        return self


class FlightReport(DomainModel):
    report_id: Identifier
    flight_kind: FlightKind
    release: Identifier
    started_at: AwareDatetime
    completed_at: AwareDatetime
    results: tuple[ScenarioResult, ...] = Field(min_length=1)
    passed: bool
    passed_scenarios: int = Field(ge=0)

    @model_validator(mode="after")
    def report_is_ordered_and_unique(self) -> Self:
        if self.completed_at <= self.started_at:
            raise ValueError("flight completed_at must be after started_at")
        scenario_ids = [result.scenario_id for result in self.results]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("flight scenario identifiers must be unique")
        calculated_count = sum(result.passed for result in self.results)
        if self.passed_scenarios != calculated_count:
            raise ValueError("flight passed_scenarios differs from scenario results")
        if self.passed != all(result.passed for result in self.results):
            raise ValueError("flight passed flag differs from scenario results")
        archived = [result for result in self.results if result.archive_ids]
        gateway_evidence = [result for result in self.results if result.gateway_decisions]
        if self.flight_kind is FlightKind.SECURITY and (archived or gateway_evidence):
            raise ValueError("security flight cannot contain archive or gateway evidence")
        if self.flight_kind is FlightKind.TRANSVERSAL:
            if not archived:
                raise ValueError("transversal flight requires document archive evidence")
            if not gateway_evidence:
                raise ValueError("transversal flight requires gateway decision evidence")
        return self
