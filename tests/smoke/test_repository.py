"""Repository contract tests for reproducibility and secret hygiene."""

from pathlib import Path


def test_required_project_contracts_exist() -> None:
    project_root = Path(__file__).resolve().parents[2]
    required = (
        "pyproject.toml",
        "requirements.in",
        "requirements.lock",
        ".gitignore",
        ".streamlit/config.toml",
        "docs/POC_HANDOFF.md",
        "scripts/quality.ps1",
        "src/sodif/app.py",
    )

    missing = [path for path in required if not (project_root / path).exists()]

    assert missing == []


def test_local_streamlit_secrets_are_not_present() -> None:
    project_root = Path(__file__).resolve().parents[2]

    assert not (project_root / ".streamlit" / "secrets.toml").exists()
