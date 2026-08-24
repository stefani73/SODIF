"""Signed-document ingestion tests across validation, history and archive boundaries."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from sodif.archive import (
    InMemoryArchiveRepository,
    SignedDocumentIngestionService,
    ingestion_policy,
)
from sodif.archive.sample import build_signed_sample
from sodif.documents import (
    DocumentRejected,
    DocumentRejectionCode,
    InMemoryTrustStore,
    demo_trusted_signer,
)
from sodif.documents.demo import sign_demo_revision


@dataclass(slots=True)
class AdvancingClock:
    value: datetime

    def now(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


def service(repository: InMemoryArchiveRepository) -> SignedDocumentIngestionService:
    return SignedDocumentIngestionService(
        InMemoryTrustStore((demo_trusted_signer(),)),
        repository,
        AdvancingClock(datetime(2026, 8, 24, 15, 0, tzinfo=UTC)),
        ingestion_policy(),
    )


def test_signed_sample_is_archived_and_exact_retry_is_not_duplicated() -> None:
    repository = InMemoryArchiveRepository()
    ingestion = service(repository)
    sample = build_signed_sample()

    first = ingestion.ingest(sample.content, sample.revision, sample.original_name)
    duplicate = ingestion.ingest(sample.content, sample.revision, sample.original_name)

    assert first.duplicate is False
    assert duplicate.duplicate is True
    assert duplicate.archive == first.archive
    assert repository.history(first.archive.document_id) == (first.archive,)


def test_next_signed_revision_extends_archived_history() -> None:
    repository = InMemoryArchiveRepository()
    ingestion = service(repository)
    sample = build_signed_sample()
    first = ingestion.ingest(sample.content, sample.revision, sample.original_name)
    content_v2 = sample.content.replace(b"1250.00", b"1350.00")
    revision_v2 = sign_demo_revision(
        content_v2,
        document_id=sample.revision.metadata.document_id,
        revision_number=2,
        previous_revision_digest=first.archive.content_digest,
        signed_at=sample.revision.metadata.signed_at + timedelta(minutes=1),
    )

    second = ingestion.ingest(content_v2, revision_v2, "comanda-achizitie-demo-v2.pdf")
    history = repository.history(first.archive.document_id)

    assert second.archive.revision_number == 2
    assert second.archive.previous_revision_digest == first.archive.content_digest
    assert history == (first.archive, second.archive)


def test_ingestion_rejects_bytes_not_covered_by_signature() -> None:
    repository = InMemoryArchiveRepository()
    ingestion = service(repository)
    sample = build_signed_sample()
    changed = sample.content.replace(b"1250.00", b"9250.00")

    with pytest.raises(DocumentRejected) as captured:
        ingestion.ingest(changed, sample.revision, sample.original_name)

    assert captured.value.code is DocumentRejectionCode.CONTENT_DIGEST_MISMATCH
    assert repository.history(sample.revision.metadata.document_id) == ()
