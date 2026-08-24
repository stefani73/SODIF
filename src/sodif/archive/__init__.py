"""Document archive contracts, services and local repositories."""

from sodif.archive.errors import (
    ArchiveConflict,
    ArchiveError,
    ArchiveIntegrityError,
    ArchiveNotFound,
)
from sodif.archive.ingestion import (
    IngestionReceipt,
    SignedDocumentIngestionService,
    SystemUtcClock,
    build_local_ingestion_service,
)
from sodif.archive.models import ArchiveQuery, ArchiveRecord, ArchiveSearchPage
from sodif.archive.policy import ingestion_policy
from sodif.archive.repository import (
    ArchivedDocument,
    ArchiveRepository,
    InMemoryArchiveRepository,
    SqliteArchiveRepository,
)
from sodif.archive.service import DocumentArchiveService

__all__ = [
    "ArchiveConflict",
    "ArchiveError",
    "ArchiveIntegrityError",
    "ArchiveNotFound",
    "ArchiveQuery",
    "ArchiveRecord",
    "ArchiveRepository",
    "ArchiveSearchPage",
    "ArchivedDocument",
    "DocumentArchiveService",
    "InMemoryArchiveRepository",
    "IngestionReceipt",
    "SignedDocumentIngestionService",
    "SqliteArchiveRepository",
    "SystemUtcClock",
    "build_local_ingestion_service",
    "ingestion_policy",
]
