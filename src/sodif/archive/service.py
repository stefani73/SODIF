"""Application service that archives only validated signed revisions."""

from sodif.archive.errors import ArchiveIntegrityError
from sodif.archive.models import ArchiveQuery, ArchiveRecord, ArchiveSearchPage
from sodif.archive.repository import ArchivedDocument, ArchiveRepository
from sodif.domain.canonical import sha256_bytes, sha256_digest
from sodif.domain.contracts import Clock
from sodif.domain.enums import DocumentFormat
from sodif.domain.revisions import RevisionAcceptance
from sodif.domain.types import Identifier


class DocumentArchiveService:
    """Create and retrieve integrity-bound records for accepted revisions."""

    def __init__(self, repository: ArchiveRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def archive(
        self,
        content: bytes,
        acceptance: RevisionAcceptance,
        original_name: str,
    ) -> ArchiveRecord:
        record = acceptance.record
        if sha256_bytes(content) != record.revision_digest:
            raise ArchiveIntegrityError("only the exact accepted revision can be archived")
        identity_digest = sha256_digest(
            {
                "protocol": "sodif.archive-identity/v1",
                "document_id": record.document_id,
                "revision_number": record.revision_number,
                "content_digest": record.revision_digest,
                "signature_digest": record.signature_digest,
            }
        )
        archived = ArchiveRecord(
            archive_id=f"arc-{identity_digest.removeprefix('sha256:')[:24]}",
            document_id=record.document_id,
            revision_number=record.revision_number,
            format=record.format,
            content_digest=record.revision_digest,
            signature_digest=record.signature_digest,
            signer_id=record.signer_id,
            key_id=record.key_id,
            signed_at=record.signed_at,
            accepted_at=record.accepted_at,
            archived_at=self._clock.now(),
            original_name=original_name,
            media_type=_media_type(record.format),
            size_bytes=len(content),
        )
        return self._repository.store(archived, content)

    def retrieve(self, archive_id: Identifier) -> ArchivedDocument:
        return self._repository.get(archive_id)

    def history(self, document_id: Identifier) -> tuple[ArchiveRecord, ...]:
        return self._repository.history(document_id)

    def search(self, query: ArchiveQuery) -> ArchiveSearchPage:
        return self._repository.search(query)


def _media_type(document_format: DocumentFormat) -> str:
    if document_format is DocumentFormat.PDF:
        return "application/pdf"
    raise ValueError(f"unsupported archive format: {document_format}")
