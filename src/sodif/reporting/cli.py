"""Command-line export of SODIF assurance flights."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sodif.demo.models import FlightReport
from sodif.demo.runner import run_security_flight, run_transversal_flight
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
        choices=("security", "transversal", "both"),
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
                "report_id": report.report_id,
                "passed": report.passed,
                "bundle_digest": exports.bundle.digest,
                "artifacts": resolved,
            }
        )
    summary = {
        "status": "exported",
        "flights": flights,
        "artifacts": artifact_paths,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


def _run_selected_flights(kind: str, archive_root: Path) -> tuple[FlightReport, ...]:
    reports: list[FlightReport] = []
    if kind in {"security", "both"}:
        reports.append(run_security_flight())
    if kind in {"transversal", "both"}:
        reports.append(run_transversal_flight(archive_root))
    return tuple(reports)


if __name__ == "__main__":
    main()
