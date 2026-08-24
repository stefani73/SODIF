"""Command-line export of the default assurance flight."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sodif.demo.runner import run_default_flight
from sodif.reporting.models import ExportArtifact, FlightExports
from sodif.reporting.service import build_flight_exports


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


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export SODIF assurance evidence")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("var/exports"),
        help="destination directory (default: var/exports)",
    )
    arguments = parser.parse_args(argv)
    exports = build_flight_exports(run_default_flight())
    paths = write_exports(arguments.output_dir, exports)
    summary = {
        "status": "exported",
        "bundle_digest": exports.bundle.digest,
        "artifacts": [str(path.resolve()) for path in paths],
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


def _atomic_write(directory: Path, artifact: ExportArtifact) -> Path:
    destination = directory / artifact.filename
    temporary = directory / f".{artifact.filename}.tmp"
    temporary.write_bytes(artifact.data)
    temporary.replace(destination)
    return destination


if __name__ == "__main__":
    main()
