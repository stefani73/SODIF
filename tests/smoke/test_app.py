"""Streamlit smoke test executed without starting a browser or server."""

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


def test_streamlit_application_boots_without_exceptions() -> None:
    project_root = Path(__file__).resolve().parents[2]
    application = project_root / "src" / "sodif" / "app.py"

    app = AppTest.from_file(str(application)).run(timeout=15)

    assert not app.exception
    assert app.radio[0].value == "Prezentare"
    assert app.button[0].label == "Deschide Assurance Flight"
    copy = "\n".join(element.value for element in app.markdown)
    assert "Din document semnat în acțiune digitală de încredere." in copy
    assert "Pasul" not in copy
    assert "Release" not in copy
    assert "Python OSS" not in copy


def test_assurance_flight_runs_and_exposes_product_decisions() -> None:
    project_root = Path(__file__).resolve().parents[2]
    application = project_root / "src" / "sodif" / "app.py"
    app = AppTest.from_file(str(application)).run(timeout=15)

    app.radio[0].set_value("Assurance Flight").run(timeout=15)

    assert not app.exception
    assert app.button[0].label == "Pornește verificarea"
    assert len(app.selectbox) == 0

    app.button[0].click().run(timeout=15)

    assert not app.exception
    assert app.selectbox[0].label == "Alege situația analizată"
    copy = "\n".join(element.value for element in app.markdown)
    assert "Toate controalele au răspuns conform politicii" in copy
    assert "Comandă autentică și neambiguă" in copy
    assert "Dovezile sunt pregătite pentru preluare" in copy
    assert len(app.get("download_button")) == 4
    assert "cost" not in copy.casefold()
    assert "v1_targeted" not in copy
