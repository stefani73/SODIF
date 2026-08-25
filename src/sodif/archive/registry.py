"""Read-only document registry composed over the verifiable archive."""

from dataclasses import dataclass
from pathlib import Path

from sodif.archive.models import ArchiveQuery, ArchiveRecord, ArchiveSearchPage, ArchiveSummary
from sodif.archive.repository import ArchivedDocument, ArchiveRepository, SqliteArchiveRepository
from sodif.domain.types import Identifier


@dataclass(frozen=True, slots=True)
class RegistrySelection:
    """Integrity-checked document bytes together with the complete revision chain."""

    document: ArchivedDocument
    history: tuple[ArchiveRecord, ...]


class DocumentRegistryService:
    """Expose bounded search and verified retrieval without leaking persistence details."""

    def __init__(self, repository: ArchiveRepository) -> None:
        self._repository = repository

    def summary(self) -> ArchiveSummary:
        return self._repository.summary()

    def search(self, query: ArchiveQuery) -> ArchiveSearchPage:
        return self._repository.search(query)

    def open(self, archive_id: Identifier) -> RegistrySelection:
        document = self._repository.get(archive_id)
        history = self._repository.history(document.record.document_id)
        return RegistrySelection(document=document, history=history)


def build_local_registry_service(archive_root: Path) -> DocumentRegistryService:
    """Build the local registry on the same durable archive used by ingestion and flight."""
    return DocumentRegistryService(SqliteArchiveRepository(archive_root))
