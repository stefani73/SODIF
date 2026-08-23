"""Tests for the fail-closed workflow state machine."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from sodif.domain.enums import ProcessingStage
from sodif.domain.errors import InvalidTransition
from sodif.domain.state import WorkflowState, WorkflowTransition, transition

START = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def test_nominal_flow_reaches_executed_without_mutating_prior_states() -> None:
    states = [WorkflowState(correlation_id="trace-001")]
    stages = (
        ProcessingStage.REVISION_VALIDATED,
        ProcessingStage.RISK_TRIAGED,
        ProcessingStage.VIEWS_READY,
        ProcessingStage.CONSENSUS_ACCEPTED,
        ProcessingStage.ACTION_COMPILED,
        ProcessingStage.PERMIT_ISSUED,
        ProcessingStage.EXECUTED,
    )
    for index, stage in enumerate(stages, start=1):
        states.append(transition(states[-1], stage, START + timedelta(seconds=index)))

    assert states[0].stage is ProcessingStage.RECEIVED
    assert states[-1].stage is ProcessingStage.EXECUTED
    assert len(states[-1].history) == 7


def test_escalation_can_resolve_or_block() -> None:
    received = WorkflowState(correlation_id="trace-001")
    validated = transition(received, ProcessingStage.REVISION_VALIDATED, START)
    triaged = transition(validated, ProcessingStage.RISK_TRIAGED, START + timedelta(seconds=1))
    escalated = transition(
        triaged,
        ProcessingStage.ESCALATED,
        START + timedelta(seconds=2),
        reason="high-impact",
    )
    resolved = transition(
        escalated,
        ProcessingStage.CONSENSUS_ACCEPTED,
        START + timedelta(seconds=3),
    )
    blocked = transition(escalated, ProcessingStage.BLOCKED, START + timedelta(seconds=3))

    assert escalated.history[-1].reason == "high-impact"
    assert resolved.stage is ProcessingStage.CONSENSUS_ACCEPTED
    assert blocked.stage is ProcessingStage.BLOCKED


def test_invalid_terminal_naive_and_non_monotonic_transitions_are_blocked() -> None:
    received = WorkflowState(correlation_id="trace-001")
    blocked = transition(received, ProcessingStage.BLOCKED, START)

    with pytest.raises(InvalidTransition, match="not allowed"):
        transition(received, ProcessingStage.EXECUTED, START)
    with pytest.raises(InvalidTransition, match="not allowed"):
        transition(blocked, ProcessingStage.RECEIVED, START + timedelta(seconds=1))
    with pytest.raises(InvalidTransition, match="timezone"):
        transition(received, ProcessingStage.REVISION_VALIDATED, datetime(2026, 8, 24, 9, 0))
    validated = transition(received, ProcessingStage.REVISION_VALIDATED, START)
    with pytest.raises(InvalidTransition, match="strictly increasing"):
        transition(validated, ProcessingStage.RISK_TRIAGED, START)


def test_manually_constructed_inconsistent_histories_are_rejected() -> None:
    valid_item = WorkflowTransition(
        from_stage=ProcessingStage.RECEIVED,
        to_stage=ProcessingStage.REVISION_VALIDATED,
        occurred_at=START,
    )
    disconnected = WorkflowTransition(
        from_stage=ProcessingStage.RISK_TRIAGED,
        to_stage=ProcessingStage.VIEWS_READY,
        occurred_at=START + timedelta(seconds=1),
    )
    forbidden = WorkflowTransition(
        from_stage=ProcessingStage.REVISION_VALIDATED,
        to_stage=ProcessingStage.EXECUTED,
        occurred_at=START + timedelta(seconds=1),
    )
    same_time = WorkflowTransition(
        from_stage=ProcessingStage.REVISION_VALIDATED,
        to_stage=ProcessingStage.RISK_TRIAGED,
        occurred_at=START,
    )

    with pytest.raises(ValidationError, match="not contiguous"):
        WorkflowState(
            correlation_id="trace-001",
            stage=ProcessingStage.VIEWS_READY,
            history=(valid_item, disconnected),
        )
    with pytest.raises(ValidationError, match="forbidden"):
        WorkflowState(
            correlation_id="trace-001",
            stage=ProcessingStage.EXECUTED,
            history=(valid_item, forbidden),
        )
    with pytest.raises(ValidationError, match="timestamps"):
        WorkflowState(
            correlation_id="trace-001",
            stage=ProcessingStage.RISK_TRIAGED,
            history=(valid_item, same_time),
        )
    with pytest.raises(ValidationError, match="final history"):
        WorkflowState(
            correlation_id="trace-001",
            stage=ProcessingStage.RECEIVED,
            history=(valid_item,),
        )
