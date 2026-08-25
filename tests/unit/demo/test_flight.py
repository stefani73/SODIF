"""Acceptance tests for the complete deterministic scenario flight."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from sodif.archive import ArchiveQuery, SqliteArchiveRepository
from sodif.demo.adapters import ScenarioSemanticAdapter
from sodif.demo.cli import main
from sodif.demo.fixtures import accepted_values, purchase_order_schema
from sodif.demo.models import (
    FlightKind,
    FlightReport,
    FlightScenario,
    ScenarioOutcome,
    ScenarioResult,
)
from sodif.demo.runner import (
    FlightRunner,
    run_archived_flight,
    run_default_flight,
    run_integrated_memory_flight,
)
from sodif.domain.enums import ProcessingStage, VerificationLevel, ViewKind
from sodif.domain.models import DocumentEnvelope


def indexed(report: FlightReport) -> dict[FlightScenario, ScenarioResult]:
    return {result.scenario_id: result for result in report.results}


def test_default_flight_covers_the_minimal_security_catalog() -> None:
    report = run_default_flight()
    scenarios = indexed(report)

    assert report.passed is True
    assert report.flight_kind is FlightKind.SECURITY
    assert report.passed_scenarios == 6
    assert tuple(scenarios) == tuple(FlightScenario)
    assert scenarios[FlightScenario.HAPPY_PATH].observed_outcome is ScenarioOutcome.EXECUTED
    assert scenarios[FlightScenario.ADAPTIVE_RECOVERY].observed_outcome is ScenarioOutcome.EXECUTED
    assert scenarios[FlightScenario.TAMPERED_DOCUMENT].rejection_code == "content_digest_mismatch"
    assert scenarios[FlightScenario.SEMANTIC_CONFLICT].rejection_code == "semantic-conflict"
    assert scenarios[FlightScenario.ACTION_TAMPERING].rejection_code == "action_mismatch"
    assert scenarios[FlightScenario.REPLAY_ATTACK].rejection_code == "permit_replayed"
    assert all(result.archive_id is None for result in report.results)
    assert all(
        "document-archived" not in {item.stage for item in result.observations}
        for result in report.results
    )


def test_flight_proves_optimization_and_bounded_escalation() -> None:
    scenarios = indexed(FlightRunner().run())
    happy = scenarios[FlightScenario.HAPPY_PATH]
    recovery = scenarios[FlightScenario.ADAPTIVE_RECOVERY]

    assert happy.verification is not None
    assert happy.verification.final_level is VerificationLevel.V1_TARGETED
    assert happy.verification.total_cost_units == 4
    assert happy.verification.saved_cost_units == 2
    assert recovery.verification is not None
    assert recovery.verification.final_level is VerificationLevel.V2_EXTENDED
    assert recovery.verification.total_cost_units == 6
    assert recovery.receipt is not None


def test_blocked_and_escalated_scenarios_never_produce_receipts() -> None:
    report = run_default_flight()

    for result in report.results:
        if result.observed_outcome is ScenarioOutcome.EXECUTED:
            assert result.workflow.stage is ProcessingStage.EXECUTED
            assert result.receipt is not None
        else:
            assert result.receipt is None
            assert result.workflow.stage in {ProcessingStage.BLOCKED, ProcessingStage.ESCALATED}


def test_flight_is_reproducible_and_serializable() -> None:
    first = run_default_flight()
    second = run_default_flight()
    serialized = first.model_dump_json(exclude_computed_fields=True)
    restored = FlightReport.model_validate_json(serialized)

    assert first == second
    assert restored.model_dump_json(exclude_computed_fields=True) == serialized


def test_product_flight_persists_a_deduplicated_revision_chain(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"

    report = run_archived_flight(archive_root)
    page = SqliteArchiveRepository(archive_root).search(ArchiveQuery())

    assert report.passed is True
    assert report.flight_kind is FlightKind.INTEGRATED
    assert page.total == 2
    assert {record.document_id for record in page.records} == {"doc-flight-001"}
    assert {record.revision_number for record in page.records} == {1, 2}
    assert {result.archive_id for result in report.results if result.archive_id is not None} == {
        record.archive_id for record in page.records
    }


def test_integrated_memory_flight_adds_archive_evidence_without_changing_decisions() -> None:
    security = run_default_flight()
    integrated = run_integrated_memory_flight()

    assert [item.observed_outcome for item in integrated.results] == [
        item.observed_outcome for item in security.results
    ]
    archived = [
        result
        for result in integrated.results
        if result.scenario_id is not FlightScenario.TAMPERED_DOCUMENT
    ]
    assert all(result.archive_id is not None for result in archived)
    happy = next(result for result in archived if result.scenario_id is FlightScenario.HAPPY_PATH)
    assert len(happy.archive_ids) == 2
    assert all(len(result.archive_ids) == 1 for result in archived if result is not happy)
    assert all(
        "document-archived" in {item.stage for item in result.observations} for result in archived
    )


def test_cli_prints_a_passing_json_report(capsys: CaptureFixture[str]) -> None:
    main()
    output = capsys.readouterr().out
    report = FlightReport.model_validate_json(output)

    assert report.passed is True
    assert report.flight_kind is FlightKind.SECURITY
    assert report.release == "0.15.0-platform1"


def test_scenario_adapter_rejects_invalid_configuration_or_empty_projection() -> None:
    try:
        ScenarioSemanticAdapter(ViewKind.STRUCTURAL, 0, accepted_values())
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("zero-cost adapter was unexpectedly accepted")

    adapter = ScenarioSemanticAdapter(
        ViewKind.STRUCTURAL,
        1,
        {"unknown": next(iter(accepted_values().values()))},
    )
    placeholder = DocumentEnvelope.model_construct(
        document_id="doc-001",
        revision_digest=f"sha256:{'a' * 64}",
    )
    try:
        adapter.extract(placeholder, b"pdf", purchase_order_schema())
    except ValueError as exc:
        assert "no schema fields" in str(exc)
    else:
        raise AssertionError("empty scenario projection was unexpectedly accepted")
