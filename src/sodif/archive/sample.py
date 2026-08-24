"""Self-contained signed sample package for the product ingestion page."""

from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from sodif.demo.fixtures import BASE_PDF
from sodif.documents.demo import DEMO_SIGNED_AT, sign_demo_revision
from sodif.domain.revisions import SignedRevision

SAMPLE_PDF_NAME = "comanda-achizitie-demo.pdf"
SAMPLE_SIGNATURE_NAME = "comanda-achizitie-demo.signature.json"
SAMPLE_ZIP_NAME = "sodif-document-semnat.zip"
SAMPLE_DOCUMENT_ID = "doc-ingestion-demo-001"
_ZIP_TIMESTAMP = (2026, 8, 24, 14, 0, 0)


@dataclass(frozen=True, slots=True)
class SignedSample:
    original_name: str
    content: bytes
    revision: SignedRevision
    package: bytes


def build_signed_sample() -> SignedSample:
    """Build the deterministic PDF, detached signature and portable ZIP package."""
    revision = sign_demo_revision(
        BASE_PDF,
        document_id=SAMPLE_DOCUMENT_ID,
        signed_at=DEMO_SIGNED_AT - timedelta(hours=12),
    )
    signature = (revision.model_dump_json(indent=2) + "\n").encode()
    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        _write_zip_entry(archive, SAMPLE_PDF_NAME, BASE_PDF)
        _write_zip_entry(archive, SAMPLE_SIGNATURE_NAME, signature)
    return SignedSample(SAMPLE_PDF_NAME, BASE_PDF, revision, output.getvalue())


def _write_zip_entry(archive: ZipFile, name: str, data: bytes) -> None:
    info = ZipInfo(name, _ZIP_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)
