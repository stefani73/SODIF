"""Application service accepting only trusted, chain-consistent signed revisions."""

from sodif.documents.content import DocumentContentPolicy, validate_document_content
from sodif.documents.crypto import InMemoryTrustStore, verify_revision_signature
from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.documents.repository import RevisionRepository
from sodif.domain.contracts import Clock
from sodif.domain.errors import InvalidRevisionChain
from sodif.domain.models import DocumentEnvelope, PolicyReference
from sodif.domain.revisions import RevisionAcceptance, RevisionRecord, SignedRevision


class SignedRevisionService:
    """Orchestrate binary, trust, signature and revision-chain validation."""

    def __init__(
        self,
        trust_store: InMemoryTrustStore,
        repository: RevisionRepository,
        clock: Clock,
        content_policy: DocumentContentPolicy | None = None,
    ) -> None:
        self._trust_store = trust_store
        self._repository = repository
        self._clock = clock
        self._content_policy = content_policy or DocumentContentPolicy()

    def validate(
        self,
        content: bytes,
        revision: SignedRevision,
        policy: PolicyReference,
    ) -> RevisionAcceptance:
        metadata = revision.metadata
        actual_digest = validate_document_content(content, metadata.format, self._content_policy)
        if actual_digest != metadata.content_digest:
            raise DocumentRejected(
                DocumentRejectionCode.CONTENT_DIGEST_MISMATCH,
                "uploaded bytes differ from the content covered by the signature",
            )

        accepted_at = self._clock.now()
        evidence, signature_digest = verify_revision_signature(
            revision,
            self._trust_store,
            accepted_at,
        )
        envelope = DocumentEnvelope(
            document_id=metadata.document_id,
            format=metadata.format,
            revision_digest=actual_digest,
            signatures=(evidence,),
            policy=policy,
            ingested_at=accepted_at,
        )
        record = RevisionRecord(
            document_id=metadata.document_id,
            revision_number=metadata.revision_number,
            format=metadata.format,
            revision_digest=actual_digest,
            previous_revision_digest=metadata.previous_revision_digest,
            signature_digest=signature_digest,
            signer_id=metadata.signer_id,
            key_id=metadata.key_id,
            signed_at=metadata.signed_at,
            accepted_at=accepted_at,
        )
        try:
            self._repository.append(record)
        except InvalidRevisionChain as exc:
            existing = next(
                (
                    item
                    for item in self._repository.history(metadata.document_id)
                    if _same_signed_revision(item, record)
                ),
                None,
            )
            if existing is not None:
                return RevisionAcceptance(envelope=envelope, record=existing, duplicate=True)
            raise DocumentRejected(
                DocumentRejectionCode.REVISION_CHAIN_INVALID,
                str(exc),
            ) from exc
        return RevisionAcceptance(envelope=envelope, record=record)


def _same_signed_revision(existing: RevisionRecord, candidate: RevisionRecord) -> bool:
    return (
        existing.document_id,
        existing.revision_number,
        existing.format,
        existing.revision_digest,
        existing.previous_revision_digest,
        existing.signature_digest,
        existing.signer_id,
        existing.key_id,
        existing.signed_at,
    ) == (
        candidate.document_id,
        candidate.revision_number,
        candidate.format,
        candidate.revision_digest,
        candidate.previous_revision_digest,
        candidate.signature_digest,
        candidate.signer_id,
        candidate.key_id,
        candidate.signed_at,
    )
