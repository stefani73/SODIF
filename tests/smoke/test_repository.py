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
        "docs/STEP_06_FLIGHT_ENGINE.md",
        "docs/STEP_07_PRODUCT_UI.md",
        "docs/STEP_08_REPORTING_EXPORTS.md",
        "docs/STEP_09_MULTIPAGE_PRODUCT.md",
        "docs/DMS_D1_ARCHIVE_INDEX.md",
        "docs/DMS_D2_DOCUMENT_INGESTION.md",
        "docs/DMS_D3_DOCUMENT_REGISTRY.md",
        "scripts/quality.ps1",
        "src/sodif/app.py",
        "src/sodif/archive/service.py",
        "src/sodif/archive/repository.py",
        "src/sodif/archive/ingestion.py",
        "src/sodif/archive/registry.py",
        "src/sodif/domain/models.py",
        "src/sodif/documents/service.py",
        "src/sodif/verification/service.py",
        "src/sodif/permits/crypto.py",
        "src/sodif/demo/runner.py",
        "src/sodif/ui/presentation.py",
        "src/sodif/ui/state.py",
        "src/sodif/ui/styles.py",
        "src/sodif/ui/pages/control.py",
        "src/sodif/ui/pages/evidence.py",
        "src/sodif/ui/pages/overview.py",
        "src/sodif/ui/pages/product.py",
        "src/sodif/pages/overview.py",
        "src/sodif/pages/product.py",
        "src/sodif/pages/control.py",
        "src/sodif/pages/reports.py",
        "src/sodif/pages/ingestion.py",
        "src/sodif/pages/registry.py",
        "src/sodif/reporting/service.py",
        "scripts/flight.ps1",
        "scripts/export-flight.ps1",
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
