"""Product-view tests for flight evidence."""

from sodif.demo.models import FlightScenario
from sodif.demo.runner import run_default_flight, run_transversal_memory_flight
from sodif.ui.presentation import present_flight


def test_flight_presentation_exposes_decisions_without_engine_vocabulary() -> None:
    view = present_flight(run_default_flight())
    rendered = repr(view)

    assert view.tone == "success"
    assert "Nucleul de securitate a confirmat comportamentul așteptat" in view.title
    assert all(
        control.name != "Sens aprobat" for item in view.scenarios for control in item.controls
    )
    assert "cost_units" not in rendered
    assert "v1_targeted" not in rendered
    assert "step" not in rendered.casefold()


def test_executed_scenario_presents_exact_api_evidence() -> None:
    scenario = next(
        item
        for item in present_flight(run_default_flight()).scenarios
        if item.scenario_id is FlightScenario.HAPPY_PATH
    )

    evidence = {item.label: item.value for item in scenario.evidence}
    assert scenario.verdict == "Autorizată"
    assert scenario.tone == "success"
    assert evidence["Tranzacție"] == "flight-happy-path"
    assert evidence["Nivel de control"] == "Verificare țintită"
    assert evidence["Acțiune"] == "POST /purchase-orders"
    assert "Arhivă" not in evidence
    assert evidence["Destinație"] == "erp-purchase-api"
    assert evidence["Confirmare API"] == "202"
    assert "Revizia validată a fost înregistrată în arhiva documentară." not in scenario.timeline
    comparisons = {item.label: item for item in scenario.comparisons}
    assert comparisons["Valoare totală"].conclusion == "Valoare autorizabilă: 1250.00"
    assert comparisons["Valoare totală"].observations == (
        "Structură PDF: 1250.00",
        "Randare vizuală A: 1250.00",
    )


def test_transversal_flight_presents_archive_and_gateway_evidence() -> None:
    view = present_flight(run_transversal_memory_flight())
    scenario = next(
        item for item in view.scenarios if item.scenario_id is FlightScenario.HAPPY_PATH
    )
    evidence = {item.label: item.value for item in scenario.evidence}

    assert "lanțul complet de încredere" in view.title
    assert evidence["Arhivă"].startswith("arc-")
    assert evidence["Istoric"] == "2 revizii legate"
    assert "Revizia validată a fost înregistrată în arhiva documentară." in scenario.timeline
    assert "Revizia următoare a continuat istoricul documentar" in scenario.timeline[-1]
    assert evidence["Decizie Gateway"].startswith("gateway-")
    assert evidence["Politică rută"] == "erp.purchase-orders"
    assert evidence["Rezultat Gateway"] == "Rutată"
    assert "Gateway-ul a verificat politica" in scenario.timeline[-2]


def test_each_protection_case_has_a_distinct_fail_closed_decision() -> None:
    scenarios = {item.scenario_id: item for item in present_flight(run_default_flight()).scenarios}

    assert scenarios[FlightScenario.TAMPERED_DOCUMENT].verdict == "Blocată"
    assert scenarios[FlightScenario.SEMANTIC_CONFLICT].verdict == "Revizuire necesară"
    assert scenarios[FlightScenario.ACTION_TAMPERING].api_effect == "Cerere respinsă"
    assert scenarios[FlightScenario.REPLAY_ATTACK].api_effect == "Repetare respinsă"
    for scenario in scenarios.values():
        assert scenario.timeline
        assert scenario.evidence

    conflict = {
        item.label: item for item in scenarios[FlightScenario.SEMANTIC_CONFLICT].comparisons
    }["Valoare totală"]
    assert conflict.conclusion == "Conflict: autorizarea este suspendată"
    assert "Structură PDF: 9250.00" in conflict.observations
    assert "Randare vizuală A: 1250.00" in conflict.observations
