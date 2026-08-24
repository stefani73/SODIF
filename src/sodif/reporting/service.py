"""Build a self-verifying export package from one flight report."""

import json
from hashlib import sha256
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from sodif.demo.models import FlightReport
from sodif.reporting.docx import render_docx_report
from sodif.reporting.models import ExportArtifact, FlightExports
from sodif.reporting.serializers import serialize_audit_log, serialize_report

_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def build_flight_exports(report: FlightReport) -> FlightExports:
    """Create human-readable and machine-readable evidence in memory."""
    document = ExportArtifact(
        "SODIF_Assurance_Flight_Report.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        render_docx_report(report),
    )
    structured = ExportArtifact(
        "sodif-flight-report.json",
        "application/json",
        serialize_report(report),
    )
    audit = ExportArtifact(
        "sodif-audit-log.ndjson",
        "application/x-ndjson",
        serialize_audit_log(report),
    )
    core_artifacts = (document, structured, audit)
    manifest = ExportArtifact(
        "sodif-evidence-manifest.json",
        "application/json",
        _build_manifest(report, core_artifacts),
    )
    bundle = ExportArtifact(
        "SODIF_Evidence_Package.zip",
        "application/zip",
        _build_bundle((*core_artifacts, manifest)),
    )
    return FlightExports(document, structured, audit, manifest, bundle)


def _build_manifest(report: FlightReport, artifacts: tuple[ExportArtifact, ...]) -> bytes:
    file_records = [
        {
            "path": artifact.filename,
            "media_type": artifact.media_type,
            "bytes": artifact.size,
            "digest": artifact.digest,
        }
        for artifact in artifacts
    ]
    evidence_root = sha256(
        "\n".join(artifact.digest for artifact in artifacts).encode()
    ).hexdigest()
    payload = {
        "protocol": "sodif.evidence-manifest/v1",
        "report_id": report.report_id,
        "release": report.release,
        "sealed_at": report.completed_at.isoformat().replace("+00:00", "Z"),
        "evidence_root": f"sha256:{evidence_root}",
        "files": file_records,
    }
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _build_bundle(artifacts: tuple[ExportArtifact, ...]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for artifact in sorted(artifacts, key=lambda item: item.filename):
            info = ZipInfo(artifact.filename, date_time=_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o600 << 16
            archive.writestr(info, artifact.data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()
