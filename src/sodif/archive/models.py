"""Typed contracts for archived signed-document revisions."""

from typing import Literal, Self

from pydantic import AwareDatetime, Field, field_validator, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import DocumentFormat, DocumentSecurityMode
from sodif.domain.types import Digest, Identifier


class ArchiveRecord(DomainModel):
    """Immutable metadata for one accepted and archived document revision."""

    protocol: Literal["sodif.archive-record/v1"] = "sodif.archive-record/v1"
    archive_id: Identifier
    document_id: Identifier
    revision_number: int = Field(ge=1)
    format: DocumentFormat
    security_mode: DocumentSecurityMode = DocumentSecurityMode.ADVANCED
    content_digest: Digest
    signature_digest: Digest
    previous_revision_digest: Digest | None = None
    signer_id: Identifier
    key_id: Identifier
    signed_at: AwareDatetime
    accepted_at: AwareDatetime
    archived_at: AwareDatetime
    original_name: str = Field(min_length=1, max_length=255)
    media_type: str = Field(min_length=3, max_length=100)
    size_bytes: int = Field(ge=1)

    @field_validator("original_name")
    @classmethod
    def original_name_is_metadata_only(cls, value: str) -> str:
        if value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
            raise ValueError("original_name must be a plain file name without a path")
        return value

    @model_validator(mode="after")
    def lifecycle_and_media_type_are_consistent(self) -> Self:
        if self.signed_at > self.accepted_at:
            raise ValueError("signed_at cannot be after accepted_at")
        if self.accepted_at > self.archived_at:
            raise ValueError("accepted_at cannot be after archived_at")
        if self.format is DocumentFormat.PDF and self.media_type != "application/pdf":
            raise ValueError("PDF archive records must use application/pdf")
        return self


class ArchiveQuery(DomainModel):
    """Bounded query used by archive explorers and service integrations."""

    text: str = Field(default="", max_length=200)
    document_id: Identifier | None = None
    signer_id: Identifier | None = None
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ArchiveSearchPage(DomainModel):
    """Stable paginated result returned by every archive implementation."""

    records: tuple[ArchiveRecord, ...]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)

    @model_validator(mode="after")
    def page_cannot_exceed_total_or_limit(self) -> Self:
        if len(self.records) > self.limit:
            raise ValueError("archive page contains more records than its limit")
        if len(self.records) > self.total:
            raise ValueError("archive page contains more records than the total")
        return self


class ArchiveSummary(DomainModel):
    """Aggregate archive facts displayed by registry clients."""

    total_documents: int = Field(ge=0)
    total_revisions: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    signer_ids: tuple[Identifier, ...]
    latest_archived_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def totals_are_consistent(self) -> Self:
        if self.total_documents > self.total_revisions:
            raise ValueError("archive cannot contain more documents than revisions")
        if self.total_revisions == 0 and (
            self.total_documents != 0
            or self.total_bytes != 0
            or self.signer_ids
            or self.latest_archived_at is not None
        ):
            raise ValueError("an empty archive cannot expose aggregate values")
        return self
