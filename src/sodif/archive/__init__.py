"""Document archive contracts, services and local repositories."""

from sodif.archive.errors import (
    ArchiveConflict,
    ArchiveError,
    ArchiveIntegrityError,
    ArchiveNotFound,
)
from sodif.archive.evidence import (
    DocumentEvidencePackage,
    DocumentEvidenceVerification,
    build_document_evidence_package,
    verify_document_evidence_package,
)
from sodif.archive.ingestion import (
    IngestionReceipt,
    SignedDocumentIngestionService,
    SystemUtcClock,
    build_local_ingestion_service,
)
from sodif.archive.models import ArchiveQuery, ArchiveRecord, ArchiveSearchPage, ArchiveSummary
from sodif.archive.policy import ingestion_policy
from sodif.archive.registry import (
    DocumentRegistryService,
    RegistrySelection,
    build_local_registry_service,
)
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
    "ArchiveSummary",
    "ArchivedDocument",
    "DocumentArchiveService",
    "DocumentEvidencePackage",
    "DocumentEvidenceVerification",
    "DocumentRegistryService",
    "InMemoryArchiveRepository",
    "IngestionReceipt",
    "RegistrySelection",
    "SignedDocumentIngestionService",
    "SqliteArchiveRepository",
    "SystemUtcClock",
    "build_document_evidence_package",
    "build_local_ingestion_service",
    "build_local_registry_service",
    "ingestion_policy",
    "verify_document_evidence_package",
]
