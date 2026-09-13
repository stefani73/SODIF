"""Session-scoped persistence for completed product runs."""

from dataclasses import dataclass
from pathlib import Path

from sodif.demo.models import FlightReport
from sodif.reporting.files import write_exports
from sodif.reporting.ledger import (
    RunLedgerEntry,
    RunLedgerIntegrityError,
    RunLedgerVerification,
    append_run_ledger,
    verify_run_ledger,
)
from sodif.reporting.models import FlightExports


@dataclass(frozen=True, slots=True)
class PersistedFlightRun:
    """Local location and files written for one completed run."""

    directory: Path
    artifacts: tuple[Path, ...]
    ledger_path: Path
    ledger_receipt: Path
    ledger_entry: RunLedgerEntry
    ledger_verification: RunLedgerVerification


def persist_flight_run(
    export_root: Path,
    report: FlightReport,
    exports: FlightExports,
) -> PersistedFlightRun:
    """Write a complete package and register it in the tamper-evident run ledger."""
    current = verify_run_ledger(export_root)
    if not current.valid:
        details = "; ".join(current.errors)
        raise RunLedgerIntegrityError(f"run integrity ledger verification failed: {details}")
    directory = (
        export_root / report.configuration.session_id / report.flight_kind.value / report.report_id
    )
    artifacts = write_exports(directory, exports)
    registration = append_run_ledger(export_root, directory, report, exports)
    return PersistedFlightRun(
        directory=directory,
        artifacts=(*artifacts, registration.receipt_path),
        ledger_path=registration.ledger_path,
        ledger_receipt=registration.receipt_path,
        ledger_entry=registration.entry,
        ledger_verification=registration.verification,
    )
