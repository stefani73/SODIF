"""Architecture and protocol tests for the domain boundary."""

import ast
from datetime import UTC, datetime
from pathlib import Path

from sodif.domain import DocumentFormat, sha256_digest
from sodif.domain.contracts import Clock, EvidenceSink
from sodif.domain.models import EvidenceEvent


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


class MemoryEvidenceSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, EvidenceEvent]] = []

    def append(self, correlation_id: str, event: EvidenceEvent) -> None:
        self.events.append((correlation_id, event))


def test_runtime_protocols_support_replaceable_adapters() -> None:
    clock = FixedClock()
    sink = MemoryEvidenceSink()

    assert isinstance(clock, Clock)
    assert isinstance(sink, EvidenceSink)
    assert not isinstance(object(), Clock)


def test_domain_package_has_no_streamlit_or_ui_dependency() -> None:
    project_root = Path(__file__).resolve().parents[3]
    domain_root = project_root / "src" / "sodif" / "domain"
    imported_roots: set[str] = set()
    for source_file in domain_root.glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

    assert "streamlit" not in imported_roots
    assert "sodif.ui" not in imported_roots


def test_domain_public_api_exposes_stable_primitives() -> None:
    assert DocumentFormat.PDF.value == "pdf"
    assert sha256_digest({"step": 2}).startswith("sha256:")
