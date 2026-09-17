"""Signed-document ingestion coordinated with the persistent archive."""

from datetime import UTC, datetime
from pathlib import Path
from threading import RLock

from sodif.archive.errors import ArchiveConflict
from sodif.archive.models import ArchiveRecord
from sodif.archive.policy import ingestion_policy
from sodif.archive.repository import ArchiveRepository, SqliteArchiveRepository
from sodif.archive.service import DocumentArchiveService
from sodif.documents import InMemoryRevisionRepository, InMemoryTrustStore, SignedRevisionService
from sodif.documents.demo import demo_trusted_signer
from sodif.domain.base import DomainModel
from sodif.domain.contracts import Clock
from sodif.domain.enums import DocumentSecurityMode
from sodif.domain.models import PolicyReference
from sodif.domain.revisions import RevisionAcceptance, RevisionRecord, SignedRevision
from sodif.domain.types import Identifier


class SystemUtcClock:
    """Wall clock adapter used only at the local application boundary."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class IngestionReceipt(DomainModel):
    """Outcome returned after a signed revision is validated and archived."""

    acceptance: RevisionAcceptance
    archive: ArchiveRecord

    @property
    def duplicate(self) -> bool:
        return self.acceptance.duplicate


class SignedDocumentIngestionService:
    """Validate trust and revision history before committing bytes to the archive."""

    def __init__(
        self,
        trust_store: InMemoryTrustStore,
        archive_repository: ArchiveRepository,
        clock: Clock,
        policy: PolicyReference,
    ) -> None:
        self._trust_store = trust_store
        self._archive_repository = archive_repository
        self._clock = clock
        self._policy = policy
        self._lock = RLock()

    def ingest(
        self,
        content: bytes,
        revision: SignedRevision,
        original_name: str,
        security_mode: DocumentSecurityMode = DocumentSecurityMode.ADVANCED,
    ) -> IngestionReceipt:
        """Validate and archive one revision, recognizing exact retries idempotently."""
        with self._lock:
            revision_repository = InMemoryRevisionRepository()
            history = self._archive_repository.history(revision.metadata.document_id)
            if history and any(item.security_mode != security_mode for item in history):
                raise ArchiveConflict(
                    "security mode cannot change inside an existing document revision chain"
                )
            for archived in history:
                revision_repository.append(_revision_record(archived))
            acceptance = SignedRevisionService(
                self._trust_store,
                revision_repository,
                self._clock,
            ).validate(content, revision, self._policy)
            archived = DocumentArchiveService(
                self._archive_repository,
                self._clock,
            ).archive(content, acceptance, original_name, security_mode)
            return IngestionReceipt(acceptance=acceptance, archive=archived)

    def history(self, document_id: Identifier) -> tuple[ArchiveRecord, ...]:
        """Return the accepted chain used to determine the next admissible revision."""
        return self._archive_repository.history(document_id)


def build_local_ingestion_service(archive_root: Path) -> SignedDocumentIngestionService:
    """Build the product ingestion boundary using only local OSS components."""
    return SignedDocumentIngestionService(
        InMemoryTrustStore((demo_trusted_signer(),)),
        SqliteArchiveRepository(archive_root),
        SystemUtcClock(),
        ingestion_policy(),
    )


def _revision_record(archived: ArchiveRecord) -> RevisionRecord:
    return RevisionRecord(
        document_id=archived.document_id,
        revision_number=archived.revision_number,
        format=archived.format,
        revision_digest=archived.content_digest,
        previous_revision_digest=archived.previous_revision_digest,
        signature_digest=archived.signature_digest,
        signer_id=archived.signer_id,
        key_id=archived.key_id,
        signed_at=archived.signed_at,
        accepted_at=archived.accepted_at,
    )
