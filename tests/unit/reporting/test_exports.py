"""Acceptance tests for deterministic assurance exports."""

import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document

from sodif.demo.models import FlightReport
from sodif.demo.runner import run_default_flight
from sodif.reporting.cli import write_exports
from sodif.reporting.serializers import serialize_report
from sodif.reporting.service import build_flight_exports


def test_export_package_is_deterministic_and_self_verifying() -> None:
    report = run_default_flight()
    first = build_flight_exports(report)
    second = build_flight_exports(report)

    assert first == second
    with ZipFile(BytesIO(first.bundle.data)) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read(first.manifest.filename))
        assert names == {
            first.document.filename,
            first.report.filename,
            first.audit_log.filename,
            first.manifest.filename,
        }
        for record in manifest["files"]:
            artifact = archive.read(record["path"])
            assert record["bytes"] == len(artifact)
            assert record["digest"].startswith("sha256:")
    assert manifest["protocol"] == "sodif.evidence-manifest/v1"
    assert manifest["report_id"] == report.report_id
    assert manifest["evidence_root"].startswith("sha256:")


def test_structured_report_and_audit_log_preserve_domain_evidence() -> None:
    report = run_default_flight()
    exports = build_flight_exports(report)
    restored = FlightReport.model_validate_json(exports.report.data)
    events = [json.loads(line) for line in exports.audit_log.data.decode().splitlines()]

    assert serialize_report(restored) == exports.report.data
    assert events[0]["event_type"] == "flight.opened"
    assert events[-1]["event_type"] == "flight.sealed"
    decisions = [event for event in events if event["event_type"] == "scenario.decision"]
    assert {event["scenario"] for event in decisions} == {
        result.scenario_id.value for result in report.results
    }
    assert sum("archive_id" in event for event in decisions) == 5


def test_word_report_contains_the_decision_register_and_scenario_evidence() -> None:
    exports = build_flight_exports(run_default_flight())
    document = Document(BytesIO(exports.document.data))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    assert "RAPORT ASSURANCE FLIGHT" in text
    assert "Registrul deciziilor" in text
    assert "0.12.0-dms3" not in text
    assert "Comandă autentică și neambiguă" in text
    assert "Arhivă: arc-" in text
    assert "Document modificat după semnare" in text
    assert "Permis prezentat din nou" in text
    assert document.tables[0].rows[0].cells[0].text == "Situație"
    assert len(document.tables[0].rows) == 7


def test_cli_writer_persists_every_artifact(tmp_path: Path) -> None:
    exports = build_flight_exports(run_default_flight())
    paths = write_exports(tmp_path, exports)

    assert {path.name for path in paths} == {
        exports.document.filename,
        exports.report.filename,
        exports.audit_log.filename,
        exports.manifest.filename,
        exports.bundle.filename,
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
