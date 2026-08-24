"""Archive persistence ports and local OSS implementations."""

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from typing import Protocol, runtime_checkable

from sodif.archive.errors import ArchiveConflict, ArchiveIntegrityError, ArchiveNotFound
from sodif.archive.models import ArchiveQuery, ArchiveRecord, ArchiveSearchPage
from sodif.domain.canonical import sha256_bytes
from sodif.domain.enums import DocumentFormat
from sodif.domain.types import Identifier

_RECORD_COLUMNS = """
archive_id, document_id, revision_number, format, content_digest, signature_digest,
previous_revision_digest, signer_id, key_id, signed_at, accepted_at, archived_at,
original_name, media_type, size_bytes
"""
_SEARCH_TOKEN = re.compile(r"[\w.:-]+", flags=re.UNICODE)


@dataclass(frozen=True, slots=True)
class ArchivedDocument:
    """An archive record together with its integrity-checked immutable bytes."""

    record: ArchiveRecord
    content: bytes


@runtime_checkable
class ArchiveRepository(Protocol):
    def store(self, record: ArchiveRecord, content: bytes) -> ArchiveRecord: ...

    def get(self, archive_id: Identifier) -> ArchivedDocument: ...

    def history(self, document_id: Identifier) -> tuple[ArchiveRecord, ...]: ...

    def search(self, query: ArchiveQuery) -> ArchiveSearchPage: ...


class InMemoryArchiveRepository:
    """Thread-safe archive used by deterministic unit and flight runs."""

    def __init__(self) -> None:
        self._records: dict[str, ArchiveRecord] = {}
        self._revision_ids: dict[tuple[str, int], str] = {}
        self._objects: dict[str, bytes] = {}
        self._lock = RLock()

    def store(self, record: ArchiveRecord, content: bytes) -> ArchiveRecord:
        _validate_content(record, content)
        revision_key = (record.document_id, record.revision_number)
        with self._lock:
            existing_id = self._revision_ids.get(revision_key)
            if existing_id is not None:
                existing = self._records[existing_id]
                _require_compatible(existing, record)
                _validate_content(existing, self._objects[existing.content_digest])
                return existing
            if record.archive_id in self._records:
                raise ArchiveConflict("archive_id is already assigned to another revision")
            existing_content = self._objects.get(record.content_digest)
            if existing_content is not None and existing_content != content:
                raise ArchiveIntegrityError("content digest collision detected in archive")
            self._objects.setdefault(record.content_digest, content)
            self._records[record.archive_id] = record
            self._revision_ids[revision_key] = record.archive_id
            return record

    def get(self, archive_id: Identifier) -> ArchivedDocument:
        with self._lock:
            record = self._records.get(archive_id)
            if record is None:
                raise ArchiveNotFound(f"archive record {archive_id!r} does not exist")
            content = self._objects[record.content_digest]
            _validate_content(record, content)
            return ArchivedDocument(record, content)

    def history(self, document_id: Identifier) -> tuple[ArchiveRecord, ...]:
        with self._lock:
            return tuple(
                sorted(
                    (item for item in self._records.values() if item.document_id == document_id),
                    key=lambda item: item.revision_number,
                )
            )

    def search(self, query: ArchiveQuery) -> ArchiveSearchPage:
        with self._lock:
            records = list(self._records.values())
        if query.document_id is not None:
            records = [item for item in records if item.document_id == query.document_id]
        if query.signer_id is not None:
            records = [item for item in records if item.signer_id == query.signer_id]
        if query.text:
            needle = query.text.casefold()
            records = [
                item
                for item in records
                if needle
                in " ".join((item.document_id, item.original_name, item.signer_id)).casefold()
            ]
        records.sort(
            key=lambda item: (item.accepted_at, item.document_id, item.revision_number),
            reverse=True,
        )
        total = len(records)
        page = tuple(records[query.offset : query.offset + query.limit])
        return ArchiveSearchPage(records=page, total=total, limit=query.limit, offset=query.offset)


class SqliteArchiveRepository:
    """Content-addressed file store with a transactional SQLite metadata index."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._objects_root = self._root / "objects" / "sha256"
        self._database_path = self._root / "index.sqlite3"
        self._lock = RLock()
        self._objects_root.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @property
    def root(self) -> Path:
        return self._root

    def store(self, record: ArchiveRecord, content: bytes) -> ArchiveRecord:
        _validate_content(record, content)
        with self._lock, self._connect() as connection:
            existing = self._find_revision(
                connection,
                record.document_id,
                record.revision_number,
            )
            if existing is not None:
                _require_compatible(existing, record)
                self._read_content(existing)
                return existing
            archive_owner = connection.execute(
                f"SELECT {_RECORD_COLUMNS} FROM archive_records WHERE archive_id = ?",
                (record.archive_id,),
            ).fetchone()
            if archive_owner is not None:
                raise ArchiveConflict("archive_id is already assigned to another revision")

            self._write_content(record, content)
            connection.execute(
                """
                INSERT INTO archive_records (
                    archive_id, document_id, revision_number, format, content_digest,
                    signature_digest, previous_revision_digest, signer_id, key_id, signed_at,
                    accepted_at, archived_at, original_name, media_type, size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _record_values(record),
            )
            connection.execute(
                """
                INSERT INTO archive_records_fts (archive_id, document_id, original_name, signer_id)
                VALUES (?, ?, ?, ?)
                """,
                (record.archive_id, record.document_id, record.original_name, record.signer_id),
            )
            return record

    def get(self, archive_id: Identifier) -> ArchivedDocument:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                f"SELECT {_RECORD_COLUMNS} FROM archive_records WHERE archive_id = ?",
                (archive_id,),
            ).fetchone()
        if row is None:
            raise ArchiveNotFound(f"archive record {archive_id!r} does not exist")
        record = _row_to_record(row)
        return ArchivedDocument(record, self._read_content(record))

    def history(self, document_id: Identifier) -> tuple[ArchiveRecord, ...]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT {_RECORD_COLUMNS} FROM archive_records
                WHERE document_id = ? ORDER BY revision_number ASC
                """,
                (document_id,),
            ).fetchall()
        return tuple(_row_to_record(row) for row in rows)

    def search(self, query: ArchiveQuery) -> ArchiveSearchPage:
        predicates: list[str] = []
        parameters: list[object] = []
        if query.document_id is not None:
            predicates.append("document_id = ?")
            parameters.append(query.document_id)
        if query.signer_id is not None:
            predicates.append("signer_id = ?")
            parameters.append(query.signer_id)
        match_query = _fts_query(query.text)
        if match_query is not None:
            predicates.append(
                "archive_id IN (SELECT archive_id FROM archive_records_fts "
                "WHERE archive_records_fts MATCH ?)"
            )
            parameters.append(match_query)
        where = f" WHERE {' AND '.join(predicates)}" if predicates else ""
        with self._lock, self._connect() as connection:
            total = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM archive_records{where}",
                    parameters,
                ).fetchone()[0]
            )
            rows = connection.execute(
                f"""
                SELECT {_RECORD_COLUMNS} FROM archive_records{where}
                ORDER BY accepted_at DESC, document_id ASC, revision_number DESC
                LIMIT ? OFFSET ?
                """,
                (*parameters, query.limit, query.offset),
            ).fetchall()
        return ArchiveSearchPage(
            records=tuple(_row_to_record(row) for row in rows),
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS archive_records (
                    archive_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    revision_number INTEGER NOT NULL CHECK (revision_number >= 1),
                    format TEXT NOT NULL,
                    content_digest TEXT NOT NULL,
                    signature_digest TEXT NOT NULL,
                    previous_revision_digest TEXT,
                    signer_id TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    signed_at TEXT NOT NULL,
                    accepted_at TEXT NOT NULL,
                    archived_at TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 1),
                    UNIQUE (document_id, revision_number)
                );
                CREATE INDEX IF NOT EXISTS archive_records_document_idx
                    ON archive_records (document_id, revision_number);
                CREATE INDEX IF NOT EXISTS archive_records_digest_idx
                    ON archive_records (content_digest);
                CREATE INDEX IF NOT EXISTS archive_records_signer_idx
                    ON archive_records (signer_id, accepted_at DESC);
                CREATE VIRTUAL TABLE IF NOT EXISTS archive_records_fts USING fts5(
                    archive_id UNINDEXED, document_id, original_name, signer_id
                );
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(archive_records)").fetchall()
            }
            if "previous_revision_digest" not in columns:
                connection.execute(
                    "ALTER TABLE archive_records ADD COLUMN previous_revision_digest TEXT"
                )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _find_revision(
        connection: sqlite3.Connection,
        document_id: Identifier,
        revision_number: int,
    ) -> ArchiveRecord | None:
        row = connection.execute(
            f"""
            SELECT {_RECORD_COLUMNS} FROM archive_records
            WHERE document_id = ? AND revision_number = ?
            """,
            (document_id, revision_number),
        ).fetchone()
        return None if row is None else _row_to_record(row)

    def _object_path(self, content_digest: str) -> Path:
        hexadecimal = content_digest.removeprefix("sha256:")
        return self._objects_root / hexadecimal[:2] / f"{hexadecimal[2:]}.blob"

    def _write_content(self, record: ArchiveRecord, content: bytes) -> None:
        target = self._object_path(record.content_digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            _validate_content(record, target.read_bytes())
            return
        staging_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=".archive-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                staging_path = Path(handle.name)
            os.replace(staging_path, target)
        finally:
            if staging_path is not None and staging_path.exists():
                staging_path.unlink()

    def _read_content(self, record: ArchiveRecord) -> bytes:
        target = self._object_path(record.content_digest)
        if not target.is_file():
            raise ArchiveIntegrityError("archived content object is missing")
        content = target.read_bytes()
        _validate_content(record, content)
        return content


def _record_values(record: ArchiveRecord) -> tuple[object, ...]:
    return (
        record.archive_id,
        record.document_id,
        record.revision_number,
        record.format.value,
        record.content_digest,
        record.signature_digest,
        record.previous_revision_digest,
        record.signer_id,
        record.key_id,
        record.signed_at.isoformat(),
        record.accepted_at.isoformat(),
        record.archived_at.isoformat(),
        record.original_name,
        record.media_type,
        record.size_bytes,
    )


def _row_to_record(row: sqlite3.Row) -> ArchiveRecord:
    return ArchiveRecord(
        archive_id=row["archive_id"],
        document_id=row["document_id"],
        revision_number=row["revision_number"],
        format=DocumentFormat(row["format"]),
        content_digest=row["content_digest"],
        signature_digest=row["signature_digest"],
        previous_revision_digest=row["previous_revision_digest"],
        signer_id=row["signer_id"],
        key_id=row["key_id"],
        signed_at=datetime.fromisoformat(row["signed_at"]),
        accepted_at=datetime.fromisoformat(row["accepted_at"]),
        archived_at=datetime.fromisoformat(row["archived_at"]),
        original_name=row["original_name"],
        media_type=row["media_type"],
        size_bytes=row["size_bytes"],
    )


def _validate_content(record: ArchiveRecord, content: bytes) -> None:
    if not isinstance(content, bytes):
        raise ArchiveIntegrityError("archive content must be immutable bytes")
    if len(content) != record.size_bytes:
        raise ArchiveIntegrityError("archive content size differs from its index record")
    if sha256_bytes(content) != record.content_digest:
        raise ArchiveIntegrityError("archive content digest differs from its index record")


def _require_compatible(existing: ArchiveRecord, candidate: ArchiveRecord) -> None:
    existing_identity = (
        existing.document_id,
        existing.revision_number,
        existing.format,
        existing.content_digest,
        existing.signature_digest,
        existing.previous_revision_digest,
        existing.signer_id,
        existing.key_id,
        existing.signed_at,
        existing.media_type,
        existing.size_bytes,
    )
    candidate_identity = (
        candidate.document_id,
        candidate.revision_number,
        candidate.format,
        candidate.content_digest,
        candidate.signature_digest,
        candidate.previous_revision_digest,
        candidate.signer_id,
        candidate.key_id,
        candidate.signed_at,
        candidate.media_type,
        candidate.size_bytes,
    )
    if existing_identity != candidate_identity:
        raise ArchiveConflict("document revision conflicts with its existing archive record")


def _fts_query(text: str) -> str | None:
    tokens = _SEARCH_TOKEN.findall(text)
    if not tokens:
        return None
    return " AND ".join(f'"{token}"*' for token in tokens)
