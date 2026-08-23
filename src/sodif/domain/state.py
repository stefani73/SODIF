"""Pure, fail-closed workflow state machine."""

from datetime import datetime
from types import MappingProxyType
from typing import Self

from pydantic import AwareDatetime, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import ProcessingStage
from sodif.domain.errors import InvalidTransition
from sodif.domain.types import Identifier

_ALLOWED_TRANSITIONS = MappingProxyType(
    {
        ProcessingStage.RECEIVED: frozenset(
            {ProcessingStage.REVISION_VALIDATED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.REVISION_VALIDATED: frozenset(
            {ProcessingStage.RISK_TRIAGED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.RISK_TRIAGED: frozenset(
            {ProcessingStage.VIEWS_READY, ProcessingStage.ESCALATED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.VIEWS_READY: frozenset(
            {
                ProcessingStage.CONSENSUS_ACCEPTED,
                ProcessingStage.ESCALATED,
                ProcessingStage.BLOCKED,
            }
        ),
        ProcessingStage.ESCALATED: frozenset(
            {ProcessingStage.CONSENSUS_ACCEPTED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.CONSENSUS_ACCEPTED: frozenset(
            {ProcessingStage.ACTION_COMPILED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.ACTION_COMPILED: frozenset(
            {ProcessingStage.PERMIT_ISSUED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.PERMIT_ISSUED: frozenset(
            {ProcessingStage.EXECUTED, ProcessingStage.BLOCKED}
        ),
        ProcessingStage.EXECUTED: frozenset(),
        ProcessingStage.BLOCKED: frozenset(),
    }
)


class WorkflowTransition(DomainModel):
    from_stage: ProcessingStage
    to_stage: ProcessingStage
    occurred_at: AwareDatetime
    reason: str | None = None


class WorkflowState(DomainModel):
    correlation_id: Identifier
    stage: ProcessingStage = ProcessingStage.RECEIVED
    history: tuple[WorkflowTransition, ...] = ()

    @model_validator(mode="after")
    def history_is_contiguous(self) -> Self:
        current = ProcessingStage.RECEIVED
        previous_time: datetime | None = None
        for item in self.history:
            if item.from_stage is not current:
                raise ValueError("workflow history is not contiguous")
            if item.to_stage not in _ALLOWED_TRANSITIONS[current]:
                raise ValueError("workflow history contains a forbidden transition")
            if previous_time is not None and item.occurred_at <= previous_time:
                raise ValueError("workflow history timestamps must increase")
            current = item.to_stage
            previous_time = item.occurred_at
        if self.stage is not current:
            raise ValueError("workflow stage must match the final history item")
        return self


def transition(
    state: WorkflowState,
    to_stage: ProcessingStage,
    occurred_at: datetime,
    reason: str | None = None,
) -> WorkflowState:
    """Return a new state or fail without modifying the original object."""
    allowed = _ALLOWED_TRANSITIONS[state.stage]
    if to_stage not in allowed:
        raise InvalidTransition(f"{state.stage.value} -> {to_stage.value} is not allowed")
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise InvalidTransition("transition time must include a timezone")
    if state.history and occurred_at <= state.history[-1].occurred_at:
        raise InvalidTransition("transition time must be strictly increasing")
    item = WorkflowTransition(
        from_stage=state.stage,
        to_stage=to_stage,
        occurred_at=occurred_at,
        reason=reason,
    )
    return WorkflowState(
        correlation_id=state.correlation_id,
        stage=to_stage,
        history=(*state.history, item),
    )

