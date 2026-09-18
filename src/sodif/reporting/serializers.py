"""Stable machine-readable representations of flight evidence."""

import json
from typing import Any

from sodif.demo.models import FlightReport, ScenarioResult


def serialize_report(report: FlightReport) -> bytes:
    """Return readable, stable JSON for the complete domain report."""
    payload = report.model_dump(mode="json", exclude_computed_fields=True)
    return _json_bytes(payload, indent=2)


def serialize_audit_log(report: FlightReport) -> bytes:
    """Return ordered NDJSON events suitable for audit ingestion."""
    events: list[dict[str, Any]] = [
        {
            "event_id": f"{report.report_id}:opened",
            "event_type": "flight.opened",
            "occurred_at": report.started_at.isoformat().replace("+00:00", "Z"),
            "report_id": report.report_id,
            "flight_kind": report.flight_kind,
            "security_mode": report.security_mode,
            "release": report.release,
            "source_tag": report.source_tag,
            "source_revision": report.source_revision,
            "session_id": report.configuration.session_id,
            "organization": report.configuration.organization_name,
            "workspace": report.configuration.workspace_name,
            "domain": report.configuration.domain_name,
            "environment": report.configuration.environment,
            "protected_service": report.configuration.protected_service,
            "route_id": report.configuration.route_id,
            "audience": report.configuration.audience,
        }
    ]
    for result in report.results:
        events.extend(_scenario_events(report, result))
    events.append(
        {
            "event_id": f"{report.report_id}:sealed",
            "event_type": "flight.sealed",
            "occurred_at": report.completed_at.isoformat().replace("+00:00", "Z"),
            "report_id": report.report_id,
            "flight_kind": report.flight_kind,
            "security_mode": report.security_mode,
            "outcome": "conform" if report.passed else "neconform",
            "release": report.release,
            "source_tag": report.source_tag,
            "source_revision": report.source_revision,
            "session_id": report.configuration.session_id,
        }
    )
    lines = (
        json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for event in events
    )
    return ("\n".join(lines) + "\n").encode()


def _scenario_events(report: FlightReport, result: ScenarioResult) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for observation in result.observations:
        event: dict[str, Any] = {
            "event_id": f"{report.report_id}:{result.scenario_id}:{observation.sequence}",
            "event_type": "scenario.observation",
            "occurred_at": observation.occurred_at.isoformat().replace("+00:00", "Z"),
            "report_id": report.report_id,
            "scenario": result.scenario_id,
            "transaction_id": result.workflow.correlation_id,
            "stage": observation.stage,
            "detail": observation.detail,
        }
        if observation.subject_digest is not None:
            event["subject_digest"] = observation.subject_digest
        events.append(event)
    for gateway_decision in result.gateway_decisions:
        gateway_event: dict[str, Any] = {
            "event_id": (
                f"{report.report_id}:{result.scenario_id}:gateway:{gateway_decision.decision_id}"
            ),
            "event_type": "gateway.decision",
            "occurred_at": gateway_decision.evaluated_at.isoformat().replace("+00:00", "Z"),
            "report_id": report.report_id,
            "scenario": result.scenario_id,
            "transaction_id": result.workflow.correlation_id,
            "decision_id": gateway_decision.decision_id,
            "request_id": gateway_decision.request_id,
            "request_digest": gateway_decision.request_digest,
            "permit_id": gateway_decision.permit_id,
            "route_id": gateway_decision.route_id,
            "audience": gateway_decision.audience,
            "status": gateway_decision.status,
            "code": gateway_decision.code,
            "observed_action_digest": gateway_decision.observed_action_digest,
            "authorized_action_digest": gateway_decision.authorized_action_digest,
            "checks": [
                {"code": check.code, "outcome": check.outcome} for check in gateway_decision.checks
            ],
        }
        if gateway_decision.receipt is not None:
            gateway_event["execution_id"] = gateway_decision.receipt.execution_id
            gateway_event["response_digest"] = gateway_decision.receipt.response_digest
        events.append(gateway_event)
    events.sort(key=lambda event: (event["occurred_at"], event["event_id"]))
    decision: dict[str, Any] = {
        "event_id": f"{report.report_id}:{result.scenario_id}:decision",
        "event_type": "scenario.decision",
        "occurred_at": result.observations[-1].occurred_at.isoformat().replace("+00:00", "Z"),
        "report_id": report.report_id,
        "scenario": result.scenario_id,
        "transaction_id": result.workflow.correlation_id,
        "outcome": result.observed_outcome,
        "workflow_state": result.workflow.stage,
        "security_mode": report.security_mode,
    }
    if result.permit_id is not None:
        decision["permit_id"] = result.permit_id
    if result.challenge_digest is not None:
        decision["challenge_digest"] = result.challenge_digest
    if result.field_root is not None:
        decision["field_root"] = result.field_root
    if result.execution_proof_digest is not None:
        decision["execution_proof_digest"] = result.execution_proof_digest
    if result.gateway_decisions:
        decision["gateway_decision_ids"] = [item.decision_id for item in result.gateway_decisions]
        decision["gateway_status"] = result.gateway_decisions[-1].status
        decision["gateway_code"] = result.gateway_decisions[-1].code
    if result.archive_id is not None:
        decision["archive_id"] = result.archive_id
        decision["archive_ids"] = list(result.archive_ids)
    if result.receipt is not None:
        decision["execution_id"] = result.receipt.execution_id
        decision["response_digest"] = result.receipt.response_digest
        decision["transfer_mode"] = result.receipt.security_mode
    if result.rejection_code is not None:
        decision["reason"] = result.rejection_code
    events.append(decision)
    return events


def _json_bytes(payload: object, *, indent: int | None = None) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=indent,
            separators=None if indent is not None else (",", ":"),
        )
        + "\n"
    ).encode()
