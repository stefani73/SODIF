"""Streamlit smoke tests for the multipage product experience."""

from pathlib import Path
from unittest.mock import patch

from _pytest.monkeypatch import MonkeyPatch
from streamlit.testing.v1 import AppTest

from sodif.app import main
from sodif.archive import SqliteArchiveRepository, build_local_ingestion_service
from sodif.archive.sample import build_signed_sample_sequence
from sodif.settings import AppSettings


def test_application_entry_point_wires_settings_to_ui() -> None:
    settings = AppSettings("SODIF", "tagline", "test", "test-release")

    with (
        patch("sodif.app.load_settings", return_value=settings),
        patch("sodif.app.configure_page") as configure_page,
        patch("sodif.app.render_product_shell") as render_shell,
    ):
        main()

    configure_page.assert_called_once_with(settings)
    render_shell.assert_called_once_with(settings)


def test_product_overview_boots_with_sidebar_navigation_and_natural_copy() -> None:
    app = _application().run(timeout=15)

    assert not app.exception
    assert len(app.radio) == 0
    copy = _copy(app)
    assert "Control verificabil de la aprobarea semnată la execuția API." in copy
    assert "PLATFORMĂ DE SECURITATE CIBERNETICĂ" in copy
    assert "SODIF Security" in copy
    assert "SODIF Archive" in copy
    assert "SODIF Gateway" in copy
    assert "Procurement" not in copy
    assert "Assurance Flight" not in copy
    assert "◈" not in copy
    assert "✓" not in copy
    assert any(
        getattr(item, "label", None) == "Explorează platforma" for item in app.get("page_link")
    )


def test_product_explainer_is_a_distinct_page() -> None:
    app = _application().run(timeout=15).switch_page("pages/product.py").run(timeout=15)

    assert not app.exception
    copy = _copy(app)
    assert "Arhitectură modulară și lanț verificabil de execuție" in copy
    assert "Contractele dintre module sunt verificabile" in copy
    assert "Între aprobarea formală și sistemul care produce efectul" in copy


def test_three_product_modules_have_distinct_workspaces() -> None:
    application = _application().run(timeout=15)

    security = application.switch_page("pages/security.py").run(timeout=15)
    assert not security.exception
    assert "Protejează trecerea de la revizia semnată" in _copy(security)
    assert "Consens semantic adaptiv" in _copy(security)
    assert any(
        getattr(item, "label", None) == "Deschide Security Flight"
        for item in security.get("page_link")
    )

    archive = security.switch_page("pages/archive.py").run(timeout=15)
    assert not archive.exception
    assert "Păstrează reviziile validate" in _copy(archive)
    assert "Continuitatea reviziilor" in _copy(archive)
    assert {getattr(item, "label", None) for item in archive.get("page_link")} >= {
        "Deschide preluarea",
        "Deschide registrul",
    }

    gateway = archive.switch_page("pages/gateway.py").run(timeout=15)
    assert not gateway.exception
    assert "Aplică permisul SODIF asupra cererii API" in _copy(gateway)
    assert "Gateway Policy Studio" in _copy(gateway)
    assert "Potrivire exactă" in _copy(gateway)
    assert "Control integrabil în infrastructura API existentă" in _copy(gateway)
    assert gateway.selectbox[0].label == "Tranzacția evaluată"
    evaluate = next(button for button in gateway.button if button.label == "Evaluează tranzacția")
    evaluate.click().run(timeout=15)

    assert not gateway.exception
    assert "Tranzacție autorizată" in _copy(gateway)
    assert "Rutată · HTTP 202" in _copy(gateway)
    assert [getattr(item, "label", None) for item in gateway.get("download_button")] == [
        "Exportă decizia JSON"
    ]

    gateway.selectbox[0].select("Parametri modificați după aprobare").run(timeout=15)
    next(button for button in gateway.button if button.label == "Evaluează tranzacția").click().run(
        timeout=15
    )

    assert not gateway.exception
    assert "Tranzacție blocată" in _copy(gateway)
    assert "Parametrii cererii diferă" in _copy(gateway)


def test_document_ingestion_page_archives_the_signed_sample(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SODIF_ARCHIVE_ROOT", str(tmp_path / "archive"))
    app = _application().run(timeout=15).switch_page("pages/ingestion.py").run(timeout=15)

    assert not app.exception
    copy = _copy(app)
    assert "Preluare documente" in copy
    assert "Construiește un istoric semnat" in copy
    initial_button = next(
        button for button in app.button if button.label == "Arhivează revizia inițială"
    )
    revised_button = next(
        button for button in app.button if button.label == "Arhivează revizia următoare"
    )
    assert revised_button.disabled is True
    initial_button.click().run(timeout=15)

    assert not app.exception
    result_copy = _copy(app)
    assert "Document verificat și arhivat" in result_copy
    assert "Identificator arhivă" in result_copy
    revised_button = next(
        button for button in app.button if button.label == "Arhivează revizia următoare"
    )
    assert revised_button.disabled is False
    revised_button.click().run(timeout=15)

    assert not app.exception
    assert "Revizie</small><strong>2</strong>" in _copy(app)
    repository = SqliteArchiveRepository(tmp_path / "archive")
    assert len(repository.history("doc-ingestion-demo-002")) == 2


def test_document_registry_searches_and_opens_the_verified_pdf(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    archive_root = tmp_path / "archive"
    monkeypatch.setenv("SODIF_ARCHIVE_ROOT", str(archive_root))
    sequence = build_signed_sample_sequence()
    ingestion = build_local_ingestion_service(archive_root)
    ingestion.ingest(
        sequence.initial.content,
        sequence.initial.revision,
        sequence.initial.original_name,
    )
    ingestion.ingest(
        sequence.revised.content,
        sequence.revised.revision,
        sequence.revised.original_name,
    )
    app = _application().run(timeout=15).switch_page("pages/registry.py").run(timeout=15)

    assert not app.exception
    copy = _copy(app)
    assert "Registru documente" in copy
    assert "Integritate reconfirmată" in copy
    assert "Previzualizare securizată" in copy
    assert "doc-ingestion-demo-002" in copy
    assert "1 document" in copy
    assert "2 revizii găsite" in copy
    assert "doc-ingestion-demo-002 · Revizia 2" in copy
    assert [getattr(item, "label", None) for item in app.get("download_button")] == [
        "Descarcă revizia",
        "Pachet verificabil",
    ]
    search = next(item for item in app.text_input if item.label == "Document, fișier sau semnatar")
    search.set_value("document-inexistent").run(timeout=15)

    assert not app.exception
    assert app.info[0].value == "Nu există documente care corespund criteriilor selectate."


def test_operational_configuration_is_retained_and_drives_the_active_session() -> None:
    app = _application().run(timeout=15).switch_page("pages/configuration.py").run(timeout=15)

    assert not app.exception
    assert "Configurare operațională" in _copy(app)
    fields = {item.label: item for item in app.text_input}
    assert fields["Organizație"].value == "TECHSUITE"
    assert fields["Domeniu"].value == "Achiziții"
    assert fields["Politică de rutare"].value == "erp.purchase-orders"
    fields["Organizație"].set_value("TECHSUITE Labs")
    fields["Domeniu"].set_value("Aprobări operaționale")
    fields["Politică de rutare"].set_value("operations.approvals")
    fields["Audiență autorizată"].set_value("operations-api")
    fields["Resursă API"].set_value("/approvals")
    next(button for button in app.button if button.label == "Salvează configurația").click().run(
        timeout=15
    )

    assert not app.exception
    configured_copy = _copy(app)
    assert "TECHSUITE Labs" in configured_copy
    assert "Aprobări operaționale" in configured_copy
    control = app.switch_page("pages/control.py").run(timeout=15)
    next(
        button for button in control.button if button.label == "Rulează Transversal Flight"
    ).click().run(timeout=15)

    assert not control.exception
    control_copy = _copy(control)
    assert "operations.approvals" in control_copy
    assert "POST /approvals" in control_copy


def test_control_center_runs_scenarios_and_reports_page_exposes_exports(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    export_root = tmp_path / "exports"
    monkeypatch.setenv("SODIF_EXPORT_ROOT", str(export_root))
    app = _application().run(timeout=15).switch_page("pages/control.py").run(timeout=15)

    assert not app.exception
    assert [getattr(button, "label", None) for button in app.button[:2]] == [
        "Rulează Security Flight",
        "Rulează Transversal Flight",
    ]
    assert len(app.selectbox) == 0

    security_button = next(
        button for button in app.button if button.label == "Rulează Security Flight"
    )
    security_button.click().run(timeout=15)

    assert not app.exception
    assert app.selectbox[0].label == "Situația analizată"
    control_copy = _copy(app)
    assert "Nucleul de securitate a confirmat comportamentul așteptat" in control_copy
    assert "Comandă autentică și neambiguă" in control_copy
    assert "Sens aprobat" not in control_copy
    assert "Rezultatul demonstrației" not in control_copy
    assert "Dovezi verificabile" not in control_copy
    assert len(app.get("download_button")) == 0
    assert not any(
        getattr(item, "label", None) == "Deschide registrul" for item in app.get("page_link")
    )

    transversal_button = next(
        button for button in app.button if button.label == "Rulează Transversal Flight"
    )
    transversal_button.click().run(timeout=15)
    assert not app.exception
    transversal_copy = _copy(app)
    assert "Fluxul transversal a confirmat lanțul complet de încredere" in transversal_copy
    assert "Decizie Gateway" in transversal_copy
    assert "Politică rută" in transversal_copy
    assert any(
        getattr(item, "label", None) == "Deschide registrul" for item in app.get("page_link")
    )
    assert any(
        getattr(item, "label", None) == "Deschide Gateway-ul" for item in app.get("page_link")
    )

    app.switch_page("pages/reports.py").run(timeout=15)

    assert not app.exception
    report_copy = _copy(app)
    assert "Audit și exporturi" in report_copy
    assert "Arhiva rulării este disponibilă" in report_copy
    assert "Lanț criptografic verificat" in report_copy
    assert "2 rulări legate" in report_copy
    assert "Pachet de dovezi" not in report_copy
    assert [str(getattr(item, "label", "")) for item in app.get("download_button")] == [
        "Pachet complet",
        "Raport Word",
        "Date JSON",
        "Jurnal de audit",
        "Chitanță de registru",
        "Registru criptografic",
    ]
    assert "Evidence package" not in report_copy
    assert "cost" not in report_copy.casefold()
    assert "v1_targeted" not in report_copy
    assert len(list(export_root.rglob("*.zip"))) == 2
    assert len(list(export_root.rglob("*.docx"))) == 2
    assert len(list(export_root.rglob("*.ndjson"))) == 3


def test_control_center_fails_closed_when_the_run_ledger_is_modified(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    export_root = tmp_path / "exports"
    monkeypatch.setenv("SODIF_EXPORT_ROOT", str(export_root))
    app = _application().run(timeout=15).switch_page("pages/control.py").run(timeout=15)
    next(button for button in app.button if button.label == "Rulează Security Flight").click().run(
        timeout=15
    )
    ledger = export_root / "sodif-run-integrity-ledger.ndjson"
    content = ledger.read_text(encoding="utf-8")
    ledger.write_text(
        content.replace('"organization":"TECHSUITE"', '"organization":"TECHSUITX"', 1),
        encoding="utf-8",
    )

    next(
        button for button in app.button if button.label == "Rulează Transversal Flight"
    ).click().run(timeout=15)

    assert not app.exception
    assert len(app.error) == 1
    assert "Rularea a fost oprită" in app.error[0].value
    assert "Istoricul nu a fost modificat" in app.error[0].value
    assert "Fluxul transversal a confirmat" not in _copy(app)


def _application() -> AppTest:
    project_root = Path(__file__).resolve().parents[2]
    return AppTest.from_file(str(project_root / "src" / "sodif" / "app.py"))


def _copy(app: AppTest) -> str:
    return "\n".join(element.value for element in app.markdown)
