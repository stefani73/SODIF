"""Session-scoped persistence for completed product runs."""

from dataclasses import dataclass
from pathlib import Path

from sodif.demo.models import FlightReport
from sodif.reporting.cli import write_exports
from sodif.reporting.models import FlightExports


@dataclass(frozen=True, slots=True)
class PersistedFlightRun:
    """Local location and files written for one completed run."""

    directory: Path
    artifacts: tuple[Path, ...]


def persist_flight_run(
    export_root: Path,
    report: FlightReport,
    exports: FlightExports,
) -> PersistedFlightRun:
    """Write a complete, self-verifying audit package for one session run."""
    directory = (
        export_root / report.configuration.session_id / report.flight_kind.value / report.report_id
    )
    artifacts = write_exports(directory, exports)
    return PersistedFlightRun(directory=directory, artifacts=artifacts)
