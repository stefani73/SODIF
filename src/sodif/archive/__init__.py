"""Document archive contracts, services and local repositories."""

from sodif.archive.errors import (
    ArchiveConflict,
    ArchiveError,
    ArchiveIntegrityError,
    ArchiveNotFound,
)
from sodif.archive.models import ArchiveQuery, ArchiveRecord, ArchiveSearchPage
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
    "SqliteArchiveRepository",
]
