"""Portable integrity evidence for one archived document revision."""

import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any, cast
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from pydantic import ValidationError

from sodif.archive.models import ArchiveRecord
from sodif.archive.registry import RegistrySelection
from sodif.domain.canonical import sha256_bytes, sha256_digest

_MANIFEST_PATH = "manifest.json"
_HISTORY_PATH = "revision-history.json"
_INSTRUCTIONS_PATH = "VERIFY.txt"
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True, slots=True)
class DocumentEvidencePackage:
    """Download-ready evidence bundle for one verified archive selection."""

    filename: str
    data: bytes
    package_id: str
    evidence_root: str

    @property
    def digest(self) -> str:
        return sha256_bytes(self.data)


@dataclass(frozen=True, slots=True)
class DocumentEvidenceVerification:
    """Offline package verification result without repository access."""

    valid: bool
    package_id: str | None
    evidence_root: str | None
    errors: tuple[str, ...]


def build_document_evidence_package(
    selection: RegistrySelection,
) -> DocumentEvidencePackage:
    """Build a deterministic document, history and integrity-manifest bundle."""
    record = selection.document.record
    document_path = f"document/{record.original_name}"
    history = _json_bytes(
        {
            "protocol": "sodif.revision-history/v1",
            "document_id": record.document_id,
            "selected_archive_id": record.archive_id,
            "revisions": [
                item.model_dump(mode="json", exclude_computed_fields=True)
                for item in selection.history
            ],
        }
    )
    instructions = _verification_instructions(record).encode("utf-8")
    contents = {
        document_path: selection.document.content,
        _HISTORY_PATH: history,
        _INSTRUCTIONS_PATH: instructions,
    }
    catalog = [_file_record(path, contents[path]) for path in sorted(contents)]
    evidence_root = _evidence_root(record.archive_id, catalog)
    package_id = f"pkg-{evidence_root.removeprefix('sha256:')[:24]}"
    manifest = _json_bytes(
        {
            "protocol": "sodif.document-evidence/v1",
            "package_id": package_id,
            "evidence_root": evidence_root,
            "document": record.model_dump(mode="json", exclude_computed_fields=True),
            "files": catalog,
        }
    )
    contents[_MANIFEST_PATH] = manifest
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(contents):
            info = ZipInfo(path, date_time=_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o600 << 16
            archive.writestr(
                info,
                contents[path],
                compress_type=ZIP_DEFLATED,
                compresslevel=9,
            )
    return DocumentEvidencePackage(
        filename=f"SODIF_{record.document_id}_r{record.revision_number}_Evidence.zip",
        data=output.getvalue(),
        package_id=package_id,
        evidence_root=evidence_root,
    )


def verify_document_evidence_package(data: bytes) -> DocumentEvidenceVerification:
    """Verify package structure, file digests and revision-chain consistency offline."""
    errors: list[str] = []
    package_id: str | None = None
    evidence_root: str | None = None
    try:
        with ZipFile(BytesIO(data), "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                errors.append("duplicate archive paths")
            if _MANIFEST_PATH not in names:
                return DocumentEvidenceVerification(False, None, None, ("missing manifest",))
            manifest = _object(archive.read(_MANIFEST_PATH))
            package_id = _string(manifest.get("package_id"))
            evidence_root = _string(manifest.get("evidence_root"))
            if manifest.get("protocol") != "sodif.document-evidence/v1":
                errors.append("unsupported manifest protocol")
            record = _record(manifest.get("document"), errors)
            catalog = _catalog(manifest.get("files"), errors)
            expected_paths = {_MANIFEST_PATH, *(item["path"] for item in catalog)}
            if set(names) != expected_paths:
                errors.append("package file set differs from manifest")

            computed_catalog: list[dict[str, object]] = []
            for item in catalog:
                path = cast(str, item["path"])
                if path not in names:
                    continue
                content = archive.read(path)
                computed = _file_record(path, content)
                computed_catalog.append(computed)
                if computed != item:
                    errors.append(f"file integrity mismatch: {path}")

            if record is not None:
                expected_root = _evidence_root(record.archive_id, computed_catalog)
                if evidence_root != expected_root:
                    errors.append("evidence root mismatch")
                expected_package_id = f"pkg-{expected_root.removeprefix('sha256:')[:24]}"
                if package_id != expected_package_id:
                    errors.append("package identifier mismatch")
                _verify_document_and_history(archive, record, catalog, errors)
    except (BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"invalid evidence package: {exc}")
    return DocumentEvidenceVerification(not errors, package_id, evidence_root, tuple(errors))


def _verify_document_and_history(
    archive: ZipFile,
    selected: ArchiveRecord,
    catalog: list[dict[str, object]],
    errors: list[str],
) -> None:
    paths = {cast(str, item["path"]) for item in catalog}
    document_path = f"document/{selected.original_name}"
    if document_path not in paths:
        errors.append("selected document is missing")
    elif sha256_bytes(archive.read(document_path)) != selected.content_digest:
        errors.append("selected document differs from archive record")
    if _HISTORY_PATH not in paths:
        errors.append("revision history is missing")
        return
    history_payload = _object(archive.read(_HISTORY_PATH))
    if history_payload.get("protocol") != "sodif.revision-history/v1":
        errors.append("unsupported revision history protocol")
    if history_payload.get("document_id") != selected.document_id:
        errors.append("history document identifier mismatch")
    if history_payload.get("selected_archive_id") != selected.archive_id:
        errors.append("history selection mismatch")
    revisions_value = history_payload.get("revisions")
    if not isinstance(revisions_value, list) or not revisions_value:
        errors.append("revision history is empty")
        return
    try:
        revisions = tuple(_parse_archive_record(item) for item in revisions_value)
    except ValidationError:
        errors.append("revision history contains invalid records")
        return
    selected_history = next(
        (item for item in revisions if item.archive_id == selected.archive_id),
        None,
    )
    if selected_history is None:
        errors.append("selected archive record is absent from history")
    elif selected_history != selected:
        errors.append("selected archive record differs from revision history")
    for index, revision in enumerate(revisions):
        if revision.document_id != selected.document_id:
            errors.append("revision history crosses document identities")
        if revision.revision_number != index + 1:
            errors.append("revision numbers are not contiguous")
        expected_previous = None if index == 0 else revisions[index - 1].content_digest
        if revision.previous_revision_digest != expected_previous:
            errors.append("revision chain is discontinuous")


def _catalog(value: object, errors: list[str]) -> list[dict[str, object]]:
    if not isinstance(value, list):
        errors.append("manifest file catalog is invalid")
        return []
    result: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            errors.append("manifest file entry is invalid")
            continue
        path = item.get("path")
        size = item.get("bytes")
        digest = item.get("digest")
        if (
            not isinstance(path, str)
            or path.startswith(("/", "\\"))
            or ".." in path.split("/")
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
        ):
            errors.append("manifest file entry is unsafe or incomplete")
            continue
        result.append({"path": path, "bytes": size, "digest": digest})
    return result


def _record(value: object, errors: list[str]) -> ArchiveRecord | None:
    try:
        return _parse_archive_record(value)
    except ValidationError:
        errors.append("manifest document record is invalid")
        return None


def _parse_archive_record(value: object) -> ArchiveRecord:
    return ArchiveRecord.model_validate_json(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _object(data: bytes) -> dict[str, Any]:
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return cast(dict[str, Any], value)


def _string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _file_record(path: str, data: bytes) -> dict[str, object]:
    return {"path": path, "bytes": len(data), "digest": sha256_bytes(data)}


def _evidence_root(archive_id: str, catalog: list[dict[str, object]]) -> str:
    return sha256_digest(
        {
            "protocol": "sodif.document-evidence-root/v1",
            "selected_archive_id": archive_id,
            "files": catalog,
        }
    )


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


def _verification_instructions(record: ArchiveRecord) -> str:
    return (
        "SODIF — verificarea offline a pachetului documentar\n\n"
        f"Document: {record.document_id}\n"
        f"Revizie: {record.revision_number}\n\n"
        "manifest.json enumeră fiecare fișier, dimensiunea și amprenta SHA-256. "
        "revision-history.json păstrează lanțul înregistrărilor de arhivă. "
        "Verificatorul SODIF recalculează toate amprentele, rădăcina de integritate "
        "și continuitatea reviziilor fără acces la depozitul original. Validarea "
        "semnăturii documentului are loc înaintea arhivării; manifestul păstrează "
        "amprenta dovezii de semnătură asociate reviziei.\n"
    )
