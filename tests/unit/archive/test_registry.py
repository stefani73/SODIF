"""Document registry tests across summary, search and verified retrieval."""

from datetime import UTC, datetime, timedelta

from sodif.archive import (
    ArchiveQuery,
    ArchiveRecord,
    DocumentRegistryService,
    InMemoryArchiveRepository,
)
from sodif.domain.canonical import sha256_bytes
from sodif.domain.enums import DocumentFormat

NOW = datetime(2026, 8, 25, 9, 0, tzinfo=UTC)


def _record(
    content: bytes,
    document_id: str,
    revision_number: int,
    original_name: str,
    previous_digest: str | None = None,
) -> ArchiveRecord:
    digest = sha256_bytes(content)
    accepted_at = NOW + timedelta(minutes=revision_number)
    return ArchiveRecord(
        archive_id=f"arc-{document_id}-{revision_number}",
        document_id=document_id,
        revision_number=revision_number,
        format=DocumentFormat.PDF,
        content_digest=digest,
        signature_digest=sha256_bytes(b"signature:" + content),
        previous_revision_digest=previous_digest,
        signer_id="registry-signer",
        key_id="registry-key",
        signed_at=accepted_at - timedelta(minutes=1),
        accepted_at=accepted_at,
        archived_at=accepted_at + timedelta(seconds=1),
        original_name=original_name,
        media_type="application/pdf",
        size_bytes=len(content),
    )


def test_registry_summarizes_searches_and_opens_revision_history() -> None:
    repository = InMemoryArchiveRepository()
    contract_v1 = b"%PDF-1.7\ncontract v1\n%%EOF"
    contract_v2 = b"%PDF-1.7\ncontract v2\n%%EOF"
    order = b"%PDF-1.7\npurchase order\n%%EOF"
    first = _record(contract_v1, "doc-contract", 1, "contract-v1.pdf")
    second = _record(
        contract_v2,
        "doc-contract",
        2,
        "contract-v2.pdf",
        first.content_digest,
    )
    third = _record(order, "doc-order", 1, "purchase-order.pdf")
    repository.store(first, contract_v1)
    repository.store(second, contract_v2)
    repository.store(third, order)
    registry = DocumentRegistryService(repository)

    summary = registry.summary()
    page = registry.search(ArchiveQuery(text="contract", signer_id="registry-signer"))
    selection = registry.open(second.archive_id)

    assert summary.total_documents == 2
    assert summary.total_revisions == 3
    assert summary.total_bytes == len(contract_v1) + len(contract_v2) + len(order)
    assert summary.signer_ids == ("registry-signer",)
    assert summary.latest_archived_at == second.archived_at
    assert page.records == (second, first)
    assert selection.document.record == second
    assert selection.document.content == contract_v2
    assert selection.history == (first, second)


def test_empty_registry_has_a_consistent_zero_summary() -> None:
    summary = DocumentRegistryService(InMemoryArchiveRepository()).summary()

    assert summary.total_documents == 0
    assert summary.total_revisions == 0
    assert summary.total_bytes == 0
    assert summary.signer_ids == ()
    assert summary.latest_archived_at is None
