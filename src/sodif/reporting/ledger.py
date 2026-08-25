"""Tamper-evident registry for completed product runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from threading import RLock
from typing import Any

from sodif.demo.models import FlightReport
from sodif.reporting.models import FlightExports

LEDGER_FILENAME = "sodif-run-integrity-ledger.ndjson"
RECEIPT_FILENAME = "sodif-run-integrity-receipt.json"
_LEDGER_PROTOCOL = "sodif.run-integrity-ledger/v1"
_RECEIPT_PROTOCOL = "sodif.run-integrity-receipt/v1"
_LOCK = RLock()


class RunLedgerIntegrityError(RuntimeError):
    """Raised when an existing run registry no longer verifies."""


@dataclass(frozen=True, slots=True)
class RunLedgerEntry:
    """One immutable link between a completed run and its audit package."""

    sequence: int
    previous_entry_digest: str | None
    report_id: str
    session_id: str
    flight_kind: str
    organization: str
    recorded_at: str
    bundle_path: str
    bundle_digest: str
    manifest_path: str
    manifest_digest: str
    entry_digest: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "protocol": _LEDGER_PROTOCOL,
            "sequence": self.sequence,
            "previous_entry_digest": self.previous_entry_digest,
            "report_id": self.report_id,
            "session_id": self.session_id,
            "flight_kind": self.flight_kind,
            "organization": self.organization,
            "recorded_at": self.recorded_at,
            "bundle_path": self.bundle_path,
            "bundle_digest": self.bundle_digest,
            "manifest_path": self.manifest_path,
            "manifest_digest": self.manifest_digest,
        }

    def payload(self) -> dict[str, object]:
        return {**self.unsigned_payload(), "entry_digest": self.entry_digest}


@dataclass(frozen=True, slots=True)
class RunLedgerVerification:
    """Independent verification result for the complete registry."""

    entries: int
    head_digest: str | None
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class RunLedgerRegistration:
    """Registry state and receipt created for one completed run."""

    ledger_path: Path
    receipt_path: Path
    entry: RunLedgerEntry
    verification: RunLedgerVerification


def verify_run_ledger(export_root: Path) -> RunLedgerVerification:
    """Verify chain continuity and every referenced package without mutation."""
    with _LOCK:
        verification, _ = _inspect_ledger(export_root)
        return verification


def append_run_ledger(
    export_root: Path,
    run_directory: Path,
    report: FlightReport,
    exports: FlightExports,
) -> RunLedgerRegistration:
    """Append one run only when the existing registry and artifacts are intact."""
    with _LOCK:
        verification, entries = _inspect_ledger(export_root)
        if not verification.valid:
            details = "; ".join(verification.errors)
            raise RunLedgerIntegrityError(f"run integrity ledger verification failed: {details}")

        entry = _new_entry(export_root, run_directory, report, exports, entries)
        ledger_path = export_root / LEDGER_FILENAME
        existing = ledger_path.read_bytes() if ledger_path.exists() else b""
        serialized = _canonical_json(entry.payload()) + b"\n"
        _atomic_write(ledger_path, existing + serialized)

        sealed, _ = _inspect_ledger(export_root)
        if not sealed.valid or sealed.head_digest != entry.entry_digest:
            details = "; ".join(sealed.errors) or "registry head does not match the new entry"
            raise RunLedgerIntegrityError(f"run integrity ledger could not be sealed: {details}")

        receipt_path = run_directory / RECEIPT_FILENAME
        _atomic_write(receipt_path, _receipt(entry, sealed))
        return RunLedgerRegistration(ledger_path, receipt_path, entry, sealed)


def _new_entry(
    export_root: Path,
    run_directory: Path,
    report: FlightReport,
    exports: FlightExports,
    entries: tuple[RunLedgerEntry, ...],
) -> RunLedgerEntry:
    relative_directory = run_directory.relative_to(export_root)
    unsigned = {
        "protocol": _LEDGER_PROTOCOL,
        "sequence": len(entries) + 1,
        "previous_entry_digest": entries[-1].entry_digest if entries else None,
        "report_id": report.report_id,
        "session_id": report.configuration.session_id,
        "flight_kind": report.flight_kind.value,
        "organization": report.configuration.organization_name,
        "recorded_at": report.completed_at.isoformat().replace("+00:00", "Z"),
        "bundle_path": (relative_directory / exports.bundle.filename).as_posix(),
        "bundle_digest": exports.bundle.digest,
        "manifest_path": (relative_directory / exports.manifest.filename).as_posix(),
        "manifest_digest": exports.manifest.digest,
    }
    digest = _digest_payload(unsigned)
    return _entry_from_payload({**unsigned, "entry_digest": digest})


def _inspect_ledger(
    export_root: Path,
) -> tuple[RunLedgerVerification, tuple[RunLedgerEntry, ...]]:
    ledger_path = export_root / LEDGER_FILENAME
    if not ledger_path.exists():
        return RunLedgerVerification(0, None, ()), ()

    errors: list[str] = []
    entries: list[RunLedgerEntry] = []
    try:
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return RunLedgerVerification(0, None, (f"ledger cannot be read: {exc}",)), ()

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            errors.append(f"line {line_number}: empty registry entry")
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("entry must be a JSON object")
            entry = _entry_from_payload(payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            errors.append(f"line {line_number}: invalid registry entry ({exc})")
            continue

        expected_sequence = len(entries) + 1
        if entry.sequence != expected_sequence:
            errors.append(
                f"line {line_number}: sequence {entry.sequence} does not match {expected_sequence}"
            )
        expected_previous = entries[-1].entry_digest if entries else None
        if entry.previous_entry_digest != expected_previous:
            errors.append(f"line {line_number}: previous entry digest does not match")
        expected_digest = _digest_payload(entry.unsigned_payload())
        if entry.entry_digest != expected_digest:
            errors.append(f"line {line_number}: entry digest does not match its content")

        _verify_artifact(
            export_root,
            entry.bundle_path,
            entry.bundle_digest,
            line_number,
            "audit package",
            errors,
        )
        _verify_artifact(
            export_root,
            entry.manifest_path,
            entry.manifest_digest,
            line_number,
            "integrity manifest",
            errors,
        )
        entries.append(entry)

    head_digest = entries[-1].entry_digest if entries else None
    return RunLedgerVerification(len(entries), head_digest, tuple(errors)), tuple(entries)


def _entry_from_payload(payload: dict[str, Any]) -> RunLedgerEntry:
    if payload.get("protocol") != _LEDGER_PROTOCOL:
        raise ValueError("unsupported registry protocol")
    sequence = payload["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    previous = payload["previous_entry_digest"]
    if previous is not None:
        previous = _digest(previous, "previous_entry_digest")
    return RunLedgerEntry(
        sequence=sequence,
        previous_entry_digest=previous,
        report_id=_text(payload["report_id"], "report_id"),
        session_id=_text(payload["session_id"], "session_id"),
        flight_kind=_text(payload["flight_kind"], "flight_kind"),
        organization=_text(payload["organization"], "organization"),
        recorded_at=_text(payload["recorded_at"], "recorded_at"),
        bundle_path=_relative_path(payload["bundle_path"], "bundle_path"),
        bundle_digest=_digest(payload["bundle_digest"], "bundle_digest"),
        manifest_path=_relative_path(payload["manifest_path"], "manifest_path"),
        manifest_digest=_digest(payload["manifest_digest"], "manifest_digest"),
        entry_digest=_digest(payload["entry_digest"], "entry_digest"),
    )


def _verify_artifact(
    export_root: Path,
    relative_path: str,
    expected_digest: str,
    line_number: int,
    label: str,
    errors: list[str],
) -> None:
    path = export_root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved_root = export_root.resolve()
        resolved = path.resolve()
        resolved.relative_to(resolved_root)
    except (OSError, ValueError):
        errors.append(f"line {line_number}: {label} path leaves the export root")
        return
    if not resolved.is_file():
        errors.append(f"line {line_number}: {label} is missing")
        return
    observed = f"sha256:{sha256(resolved.read_bytes()).hexdigest()}"
    if observed != expected_digest:
        errors.append(f"line {line_number}: {label} digest does not match")


def _receipt(entry: RunLedgerEntry, verification: RunLedgerVerification) -> bytes:
    payload = {
        "protocol": _RECEIPT_PROTOCOL,
        "ledger": LEDGER_FILENAME,
        "sequence": entry.sequence,
        "entry_digest": entry.entry_digest,
        "previous_entry_digest": entry.previous_entry_digest,
        "verified_entries": verification.entries,
        "verified_head_digest": verification.head_digest,
        "report_id": entry.report_id,
        "bundle_path": entry.bundle_path,
        "bundle_digest": entry.bundle_digest,
        "manifest_path": entry.manifest_path,
        "manifest_digest": entry.manifest_digest,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n"


def _digest_payload(payload: dict[str, object]) -> str:
    return f"sha256:{sha256(_canonical_json(payload)).hexdigest()}"


def _canonical_json(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _atomic_write(destination: Path, data: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _digest(value: object, field: str) -> str:
    text = _text(value, field)
    prefix, separator, hexadecimal = text.partition(":")
    if separator != ":" or prefix != "sha256" or len(hexadecimal) != 64:
        raise ValueError(f"{field} must be a SHA-256 digest")
    try:
        int(hexadecimal, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be a SHA-256 digest") from exc
    return text


def _relative_path(value: object, field: str) -> str:
    text = _text(value, field)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} must stay within the export root")
    return path.as_posix()
