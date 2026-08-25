"""Self-contained signed sample package for the product ingestion page."""

from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from sodif.documents.demo import DEMO_SIGNED_AT, sign_demo_revision
from sodif.domain.canonical import sha256_bytes
from sodif.domain.revisions import SignedRevision

SAMPLE_PDF_NAME = "comanda-achizitie-demo.pdf"
SAMPLE_SIGNATURE_NAME = "comanda-achizitie-demo.signature.json"
SAMPLE_ZIP_NAME = "sodif-document-semnat.zip"
SAMPLE_REVISION_PDF_NAME = "comanda-achizitie-demo-r2.pdf"
SAMPLE_REVISION_SIGNATURE_NAME = "comanda-achizitie-demo-r2.signature.json"
SAMPLE_SEQUENCE_ZIP_NAME = "sodif-istoric-document-semnat.zip"
SAMPLE_DOCUMENT_ID = "doc-ingestion-demo-002"
_ZIP_TIMESTAMP = (2026, 8, 24, 14, 0, 0)


@dataclass(frozen=True, slots=True)
class SignedSample:
    original_name: str
    content: bytes
    revision: SignedRevision
    package: bytes


@dataclass(frozen=True, slots=True)
class SignedSampleSequence:
    """Two chain-bound revisions and their portable verification package."""

    initial: SignedSample
    revised: SignedSample
    package: bytes


def build_signed_sample() -> SignedSample:
    """Build the deterministic PDF, detached signature and portable ZIP package."""
    content = _build_sample_pdf()
    revision = sign_demo_revision(
        content,
        document_id=SAMPLE_DOCUMENT_ID,
        signed_at=DEMO_SIGNED_AT - timedelta(hours=12),
    )
    package = _signed_revision_package(
        SAMPLE_PDF_NAME,
        SAMPLE_SIGNATURE_NAME,
        content,
        revision,
    )
    return SignedSample(SAMPLE_PDF_NAME, content, revision, package)


def build_signed_sample_sequence() -> SignedSampleSequence:
    """Build a deterministic two-revision history with an exact predecessor link."""
    initial = build_signed_sample()
    content = initial.content.replace(b"1250.00", b"1350.00")
    revision = sign_demo_revision(
        content,
        document_id=SAMPLE_DOCUMENT_ID,
        revision_number=2,
        previous_revision_digest=sha256_bytes(initial.content),
        signed_at=initial.revision.metadata.signed_at + timedelta(minutes=5),
    )
    revised = SignedSample(
        SAMPLE_REVISION_PDF_NAME,
        content,
        revision,
        _signed_revision_package(
            SAMPLE_REVISION_PDF_NAME,
            SAMPLE_REVISION_SIGNATURE_NAME,
            content,
            revision,
        ),
    )
    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        _write_zip_entry(archive, f"revizia-1/{initial.original_name}", initial.content)
        _write_zip_entry(
            archive,
            f"revizia-1/{SAMPLE_SIGNATURE_NAME}",
            _signature_bytes(initial.revision),
        )
        _write_zip_entry(archive, f"revizia-2/{revised.original_name}", revised.content)
        _write_zip_entry(
            archive,
            f"revizia-2/{SAMPLE_REVISION_SIGNATURE_NAME}",
            _signature_bytes(revised.revision),
        )
    return SignedSampleSequence(initial, revised, output.getvalue())


def _signed_revision_package(
    document_name: str,
    signature_name: str,
    content: bytes,
    revision: SignedRevision,
) -> bytes:
    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        _write_zip_entry(archive, document_name, content)
        _write_zip_entry(archive, signature_name, _signature_bytes(revision))
    return output.getvalue()


def _signature_bytes(revision: SignedRevision) -> bytes:
    return (revision.model_dump_json(indent=2) + "\n").encode()


def _build_sample_pdf() -> bytes:
    """Create a small standards-compliant PDF that can be rendered by the product viewer."""
    stream = (
        b"BT\n/F1 20 Tf\n72 760 Td\n(SODIF Purchase Order) Tj\n"
        b"0 -38 Td\n/F1 11 Tf\n(Supplier: SUP-01) Tj\n"
        b"0 -22 Td\n(Total: 1250.00 EUR) Tj\n"
        b"0 -22 Td\n(Status: signed document sample) Tj\nET\n"
    )
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    )
    output = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def _write_zip_entry(archive: ZipFile, name: str, data: bytes) -> None:
    info = ZipInfo(name, _ZIP_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)
