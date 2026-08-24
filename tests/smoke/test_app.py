"""Streamlit smoke tests for the multipage product experience."""

from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from sodif.app import main
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
    assert "Din document semnat în acțiune digitală de încredere." in copy
    assert "Încredere verificabilă între document și API" in copy
    assert "Procurement" not in copy
    assert "Assurance Flight" not in copy
    assert "◈" not in copy
    assert "✓" not in copy
    assert any(
        getattr(item, "label", None) == "Deschide demonstrația" for item in app.get("page_link")
    )


def test_product_explainer_is_a_distinct_page() -> None:
    app = _application().run(timeout=15).switch_page("pages/product.py").run(timeout=15)

    assert not app.exception
    copy = _copy(app)
    assert "Cum funcționează SODIF" in copy
    assert "Decizia privește tranzacția" in copy
    assert "Înaintea sistemului care produce efectul" in copy


def test_control_center_runs_scenarios_and_reports_page_exposes_exports() -> None:
    app = _application().run(timeout=15).switch_page("pages/control.py").run(timeout=15)

    assert not app.exception
    assert app.button[0].label == "Rulează demonstrația"
    assert len(app.selectbox) == 0

    app.button[0].click().run(timeout=15)

    assert not app.exception
    assert app.selectbox[0].label == "Situația analizată"
    control_copy = _copy(app)
    assert "Toate controalele au confirmat comportamentul așteptat" in control_copy
    assert "Comandă autentică și neambiguă" in control_copy
    assert "Sens aprobat" not in control_copy
    assert len(app.get("download_button")) == 0

    app.switch_page("pages/reports.py").run(timeout=15)

    assert not app.exception
    report_copy = _copy(app)
    assert "Rapoarte și dovezi" in report_copy
    assert "Fișiere pregătite pentru preluare" in report_copy
    assert [str(getattr(item, "label", "")) for item in app.get("download_button")] == [
        "Pachet complet",
        "Raport Word",
        "Date JSON",
        "Jurnal de audit",
    ]
    assert "Evidence package" not in report_copy
    assert "cost" not in report_copy.casefold()
    assert "v1_targeted" not in report_copy


def _application() -> AppTest:
    project_root = Path(__file__).resolve().parents[2]
    return AppTest.from_file(str(project_root / "src" / "sodif" / "app.py"))


def _copy(app: AppTest) -> str:
    return "\n".join(element.value for element in app.markdown)
