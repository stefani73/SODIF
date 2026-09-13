"""Atomic persistence of generated Flight artifacts."""

from pathlib import Path

from sodif.reporting.models import ExportArtifact, FlightExports


def write_exports(output_directory: Path, exports: FlightExports) -> tuple[Path, ...]:
    """Persist every export atomically in the requested directory."""
    output_directory.mkdir(parents=True, exist_ok=True)
    artifacts = (
        exports.document,
        exports.report,
        exports.audit_log,
        exports.manifest,
        exports.bundle,
    )
    return tuple(_atomic_write(output_directory, artifact) for artifact in artifacts)


def _atomic_write(directory: Path, artifact: ExportArtifact) -> Path:
    destination = directory / artifact.filename
    temporary = directory / f".{artifact.filename}.tmp"
    temporary.write_bytes(artifact.data)
    temporary.replace(destination)
    return destination
