"""Immutable in-memory export artifacts."""

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class ExportArtifact:
    filename: str
    media_type: str
    data: bytes

    @property
    def digest(self) -> str:
        return f"sha256:{sha256(self.data).hexdigest()}"

    @property
    def size(self) -> int:
        return len(self.data)


@dataclass(frozen=True, slots=True)
class FlightExports:
    document: ExportArtifact
    report: ExportArtifact
    audit_log: ExportArtifact
    manifest: ExportArtifact
    bundle: ExportArtifact
