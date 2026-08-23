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
        patch("sodif.app.render_foundation_shell") as render_shell,
    ):
        main()

    configure_page.assert_called_once_with(settings)
    render_shell.assert_called_once_with(settings)


def test_streamlit_application_boots_without_exceptions() -> None:
    project_root = Path(__file__).resolve().parents[2]
    application = project_root / "src" / "sodif" / "app.py"

    app = AppTest.from_file(str(application)).run(timeout=15)

    assert not app.exception
    assert app.title[0].value == "SODIF"
    assert app.info[0].value.startswith("Nucleul de domeniu este validat")
