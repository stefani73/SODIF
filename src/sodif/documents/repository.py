"""Revision persistence port and thread-safe local implementation."""

from threading import RLock
from typing import Protocol, runtime_checkable

from sodif.domain.revisions import RevisionRecord, validate_revision_append
from sodif.domain.types import Identifier


@runtime_checkable
class RevisionRepository(Protocol):
    def history(self, document_id: Identifier) -> tuple[RevisionRecord, ...]: ...

    def append(self, record: RevisionRecord) -> None: ...


class InMemoryRevisionRepository:
    """Atomic process-local repository for tests and the flight demonstrator."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[RevisionRecord, ...]] = {}
        self._lock = RLock()

    def history(self, document_id: Identifier) -> tuple[RevisionRecord, ...]:
        with self._lock:
            return self._records.get(document_id, ())

    def append(self, record: RevisionRecord) -> None:
        with self._lock:
            current = self._records.get(record.document_id, ())
            validate_revision_append(current, record)
            self._records[record.document_id] = (*current, record)
