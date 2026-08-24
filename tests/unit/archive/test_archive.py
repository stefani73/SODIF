"""Contract tests for the signed-document archive and SQLite index."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from sodif.archive import (
    ArchiveConflict,
    ArchiveIntegrityError,
    ArchiveNotFound,
    ArchiveQuery,
    DocumentArchiveService,
    InMemoryArchiveRepository,
    SqliteArchiveRepository,
)
from sodif.domain.canonical import sha256_bytes
from sodif.domain.enums import DocumentFormat, SignatureStatus
from sodif.domain.models import DocumentEnvelope, PolicyReference, SignatureEvidence
from sodif.domain.revisions import RevisionAcceptance, RevisionRecord

ACCEPTED_AT = datetime(2026, 8, 24, 14, 0, tzinfo=UTC)
ARCHIVED_AT = ACCEPTED_AT + timedelta(seconds=1)
PDF_CONTENT = b"%PDF-1.7\nSODIF signed purchase order\n%%EOF"
OTHER_PDF_CONTENT = b"%PDF-1.7\nDifferent signed purchase order\n%%EOF"


@dataclass(frozen=True, slots=True)
class FixedClock:
    value: datetime

    def now(self) -> datetime:
        return self.value


def acceptance(content: bytes = PDF_CONTENT) -> RevisionAcceptance:
    digest = sha256_bytes(content)
    policy = PolicyReference(
        policy_id="archive-policy",
        version="1.0",
        digest=sha256_bytes(b"archive-policy"),
    )
    record = RevisionRecord(
        document_id="doc-archive-001",
        revision_number=1,
        format=DocumentFormat.PDF,
        revision_digest=digest,
        signature_digest=sha256_bytes(b"signature" + content),
        signer_id="trusted-signer",
        key_id="trusted-key",
        signed_at=ACCEPTED_AT - timedelta(minutes=1),
        accepted_at=ACCEPTED_AT,
    )
    envelope = DocumentEnvelope(
        document_id=record.document_id,
        format=record.format,
        revision_digest=record.revision_digest,
        signatures=(
            SignatureEvidence(
                signer_id=record.signer_id,
                status=SignatureStatus.VALID,
                covers_revision=True,
                validated_at=record.accepted_at,
                validator_id="archive-test-validator",
                validator_version="1.0",
            ),
        ),
        policy=policy,
        ingested_at=record.accepted_at,
    )
    return RevisionAcceptance(envelope=envelope, record=record)


def test_memory_archive_is_idempotent_searchable_and_integrity_checked() -> None:
    repository = InMemoryArchiveRepository()
    service = DocumentArchiveService(repository, FixedClock(ARCHIVED_AT))

    first = service.archive(PDF_CONTENT, acceptance(), "comanda-achizitie-001.pdf")
    second = service.archive(PDF_CONTENT, acceptance(), "comanda-achizitie-001.pdf")

    assert first == second
    assert first.archive_id.startswith("arc-")
    assert service.retrieve(first.archive_id).content == PDF_CONTENT
    assert service.history(first.document_id) == (first,)
    page = service.search(ArchiveQuery(text="achizitie", signer_id="trusted-signer"))
    assert page.records == (first,)
    assert page.total == 1

    with pytest.raises(ArchiveNotFound):
        service.retrieve("arc-missing")
    with pytest.raises(ArchiveIntegrityError, match="exact accepted revision"):
        service.archive(OTHER_PDF_CONTENT, acceptance(), "comanda-achizitie-001.pdf")
    with pytest.raises(ValidationError, match="plain file name"):
        service.archive(PDF_CONTENT, acceptance(), "..\\unsafe.pdf")


def test_sqlite_archive_persists_deduplicates_and_filters(tmp_path: Path) -> None:
    root = tmp_path / "document-archive"
    service = DocumentArchiveService(SqliteArchiveRepository(root), FixedClock(ARCHIVED_AT))
    stored = service.archive(PDF_CONTENT, acceptance(), "comanda-achizitie-001.pdf")

    reopened = DocumentArchiveService(SqliteArchiveRepository(root), FixedClock(ARCHIVED_AT))
    duplicate = reopened.archive(PDF_CONTENT, acceptance(), "comanda-achizitie-001.pdf")
    page = reopened.search(ArchiveQuery(text="comanda achizitie", document_id="doc-archive-001"))

    assert duplicate == stored
    assert reopened.retrieve(stored.archive_id).content == PDF_CONTENT
    assert page.records == (stored,)
    assert page.total == 1
    assert (root / "index.sqlite3").is_file()
    assert len(tuple((root / "objects").rglob("*.blob"))) == 1

    with pytest.raises(ArchiveConflict, match="conflicts"):
        reopened.archive(
            OTHER_PDF_CONTENT,
            acceptance(OTHER_PDF_CONTENT),
            "comanda-achizitie-001.pdf",
        )


def test_sqlite_archive_detects_object_tampering(tmp_path: Path) -> None:
    root = tmp_path / "document-archive"
    repository = SqliteArchiveRepository(root)
    service = DocumentArchiveService(repository, FixedClock(ARCHIVED_AT))
    stored = service.archive(PDF_CONTENT, acceptance(), "comanda-achizitie-001.pdf")
    object_path = next((root / "objects").rglob("*.blob"))
    object_path.write_bytes(b"tampered")

    with pytest.raises(ArchiveIntegrityError, match="size differs"):
        repository.get(stored.archive_id)
