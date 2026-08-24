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
            "release": report.release,
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
            "outcome": "conform" if report.passed else "neconform",
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
            "stage": observation.stage,
            "detail": observation.detail,
        }
        if observation.subject_digest is not None:
            event["subject_digest"] = observation.subject_digest
        events.append(event)
    decision: dict[str, Any] = {
        "event_id": f"{report.report_id}:{result.scenario_id}:decision",
        "event_type": "scenario.decision",
        "occurred_at": result.observations[-1].occurred_at.isoformat().replace("+00:00", "Z"),
        "report_id": report.report_id,
        "scenario": result.scenario_id,
        "outcome": result.observed_outcome,
        "workflow_state": result.workflow.stage,
    }
    if result.permit_id is not None:
        decision["permit_id"] = result.permit_id
    if result.archive_id is not None:
        decision["archive_id"] = result.archive_id
    if result.receipt is not None:
        decision["execution_id"] = result.receipt.execution_id
        decision["response_digest"] = result.receipt.response_digest
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
