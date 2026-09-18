"""Command-line export of SODIF assurance flights."""

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sodif.demo.models import FlightConfiguration, FlightReport
from sodif.demo.runner import (
    default_flight_configuration,
    run_security_flight,
    run_transversal_flight,
)
from sodif.domain.enums import DocumentSecurityMode
from sodif.reporting.files import write_exports
from sodif.reporting.service import build_flight_exports


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export SODIF assurance evidence")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("var/exports"),
        help="destination directory (default: var/exports)",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=Path("var/archive"),
        help="archive directory used by the transversal flight (default: var/archive)",
    )
    parser.add_argument(
        "--kind",
        choices=("security", "transversal", "standard", "both", "all"),
        default="both",
        help="flight selection (default: both)",
    )
    arguments = parser.parse_args(argv)
    reports = _run_selected_flights(arguments.kind, arguments.archive_root)
    flights: list[dict[str, object]] = []
    artifact_paths: list[str] = []
    for report in reports:
        exports = build_flight_exports(report)
        paths = write_exports(arguments.output_dir, exports)
        resolved = [str(path.resolve()) for path in paths]
        artifact_paths.extend(resolved)
        flights.append(
            {
                "flight_kind": report.flight_kind.value,
                "security_mode": report.security_mode.value,
                "report_id": report.report_id,
                "passed": report.passed,
                "bundle_digest": exports.bundle.digest,
                "artifacts": resolved,
            }
        )
    summary = {
        "status": "exported",
        "evidence_set_id": reports[0].configuration.session_id,
        "release": reports[0].release,
        "source_tag": reports[0].source_tag,
        "source_revision": reports[0].source_revision,
        "flights": flights,
        "artifacts": artifact_paths,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


def _run_selected_flights(kind: str, archive_root: Path) -> tuple[FlightReport, ...]:
    started_at = datetime.now(UTC)
    evidence_set_id = f"evidence-{started_at.strftime('%Y%m%dT%H%M%S%fZ')}"
    configuration: FlightConfiguration = default_flight_configuration().model_copy(
        update={"session_id": evidence_set_id}
    )
    reports: list[FlightReport] = []
    if kind in {"security", "both", "all"}:
        reports.append(run_security_flight(configuration, started_at=started_at))
    if kind in {"transversal", "both", "all"}:
        reports.append(
            run_transversal_flight(
                archive_root / "advanced" if kind == "all" else archive_root,
                configuration,
                started_at=started_at,
            )
        )
    if kind in {"standard", "all"}:
        reports.append(
            run_transversal_flight(
                archive_root / "standard" if kind == "all" else archive_root,
                configuration,
                DocumentSecurityMode.STANDARD,
                started_at=started_at,
            )
        )
    return tuple(reports)


if __name__ == "__main__":
    main()
