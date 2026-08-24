"""Repository contract tests for reproducibility and secret hygiene."""

import re
import tomllib
from pathlib import Path
from typing import cast

from sodif import __version__


def test_required_project_contracts_exist() -> None:
    project_root = Path(__file__).resolve().parents[2]
    required = (
        "pyproject.toml",
        "requirements.in",
        "requirements.lock",
        ".gitignore",
        ".streamlit/config.toml",
        "docs/POC_HANDOFF.md",
        "docs/STEP_02_DOMAIN_CORE.md",
        "docs/STEP_03_SIGNED_REVISIONS.md",
        "docs/STEP_04_ADAPTIVE_CONSENSUS.md",
        "docs/STEP_05_EXECUTION_PERMIT.md",
        "scripts/quality.ps1",
        "src/sodif/app.py",
        "src/sodif/domain/models.py",
        "src/sodif/documents/service.py",
        "src/sodif/verification/service.py",
        "src/sodif/permits/crypto.py",
    )

    missing = [path for path in required if not (project_root / path).exists()]

    assert missing == []


def test_local_streamlit_secrets_are_not_present() -> None:
    project_root = Path(__file__).resolve().parents[2]

    assert not (project_root / ".streamlit" / "secrets.toml").exists()


def test_declared_dependencies_are_locked_and_version_is_synchronized() -> None:
    project_root = Path(__file__).resolve().parents[2]
    configuration = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = cast(dict[str, object], configuration["project"])
    runtime = cast(list[str], project["dependencies"])
    optional = cast(dict[str, list[str]], project["optional-dependencies"])
    declared = runtime + optional["dev"]
    dependency_names = {
        re.split(r"[<>=!~\[]", specification, maxsplit=1)[0].lower().replace("_", "-")
        for specification in declared
    }
    locked_names = {
        line.split("==", maxsplit=1)[0].lower().replace("_", "-")
        for line in (project_root / "requirements.lock").read_text(encoding="utf-8").splitlines()
        if "==" in line and not line.startswith("#")
    }

    assert dependency_names <= locked_names
    assert project["version"] == __version__
