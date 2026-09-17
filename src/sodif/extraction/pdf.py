"""Independent PDF interpretations using pypdf, renderers and Tesseract OCR."""

import csv
import os
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pymupdf
from pypdf import PdfReader

from sodif.domain.canonical import sha256_bytes, sha256_digest
from sodif.domain.enums import ViewKind
from sodif.domain.invariance import SemanticChallenge
from sodif.domain.models import DocumentEnvelope, SemanticView
from sodif.domain.schemas import IntentSchema
from sodif.extraction.errors import DocumentExtractionError, ExtractionDependencyError
from sodif.extraction.fields import SourceLine, extract_schema_fields

_TESSERACT_FALLBACK = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


@dataclass(frozen=True, slots=True)
class VisualExtractionProfile:
    profile_id: str
    renderer: str
    dpi: int
    page_segmentation_mode: int
    languages: str = "ron+eng"

    def __post_init__(self) -> None:
        if self.renderer not in {"mupdf", "poppler"}:
            raise ValueError("visual renderer must be mupdf or poppler")
        if self.dpi < 150 or self.dpi > 600:
            raise ValueError("visual profile DPI must be between 150 and 600")
        if self.page_segmentation_mode < 3 or self.page_segmentation_mode > 13:
            raise ValueError("unsupported Tesseract page segmentation mode")


VISUAL_PROFILES = {
    "mupdf-tesseract-300-psm6-v1": VisualExtractionProfile(
        "mupdf-tesseract-300-psm6-v1",
        "mupdf",
        300,
        6,
    ),
    "poppler-tesseract-360-psm11-v1": VisualExtractionProfile(
        "poppler-tesseract-360-psm11-v1",
        "poppler",
        360,
        11,
    ),
}


def _resolve_executable(environment_name: str, command: str, fallback: Path | None = None) -> str:
    configured = os.environ.get(environment_name)
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
        raise ExtractionDependencyError(f"configured executable does not exist: {path}")
    discovered = shutil.which(command)
    if discovered:
        return discovered
    if fallback is not None and fallback.is_file():
        return str(fallback)
    raise ExtractionDependencyError(f"required executable is unavailable: {command}")


def _run(command: list[str], timeout: int = 45) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DocumentExtractionError(f"document interpreter failed: {command[0]}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        message = detail[-1] if detail else f"exit code {completed.returncode}"
        raise DocumentExtractionError(f"document interpreter rejected input: {message}")
    return completed.stdout


@lru_cache(maxsize=32)
def _structural_lines(content: bytes) -> tuple[SourceLine, ...]:
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        lines: list[SourceLine] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            for line_number, text_line in enumerate(text.splitlines(), start=1):
                if text_line.strip():
                    lines.append(
                        SourceLine(
                            page=page_number,
                            text=text_line.strip(),
                            locator=f"page={page_number};structural_line={line_number}",
                            confidence=Decimal("0.99"),
                        )
                    )
        return tuple(lines)
    except Exception as exc:
        raise DocumentExtractionError("pypdf could not interpret the signed PDF") from exc


def _mupdf_render(content: bytes, directory: Path, dpi: int) -> tuple[Path, ...]:
    try:
        document: Any = pymupdf.open(  # type: ignore[no-untyped-call]
            stream=content,
            filetype="pdf",
        )
        paths: list[Path] = []
        for page_index in range(document.page_count):
            page: Any = document.load_page(page_index)
            page_number = page_index + 1
            path = directory / f"page-{page_number:04d}.png"
            page.get_pixmap(dpi=dpi, alpha=False).save(path)
            paths.append(path)
        document.close()
        return tuple(paths)
    except Exception as exc:
        raise DocumentExtractionError("MuPDF could not render the signed PDF") from exc


def _poppler_render(content: bytes, directory: Path, dpi: int) -> tuple[Path, ...]:
    pdftoppm = _resolve_executable("SODIF_PDFTOPPM_CMD", "pdftoppm")
    source = directory / "source.pdf"
    source.write_bytes(content)
    prefix = directory / "page"
    _run([pdftoppm, "-png", "-r", str(dpi), str(source), str(prefix)])
    paths = tuple(sorted(directory.glob("page-*.png")))
    if not paths:
        raise DocumentExtractionError("Poppler produced no rendered PDF pages")
    return paths


def _ocr_lines(
    path: Path,
    page_number: int,
    profile: VisualExtractionProfile,
) -> tuple[SourceLine, ...]:
    tesseract = _resolve_executable("SODIF_TESSERACT_CMD", "tesseract", _TESSERACT_FALLBACK)
    output = _run(
        [
            tesseract,
            str(path),
            "stdout",
            "-l",
            profile.languages,
            "--psm",
            str(profile.page_segmentation_mode),
            "tsv",
        ]
    )
    grouped: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
    for row in csv.DictReader(StringIO(output), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = Decimal(row.get("conf") or "-1")
        except Exception:
            confidence = Decimal("-1")
        if text and confidence >= 0:
            key = (
                int(row.get("block_num") or 0),
                int(row.get("par_num") or 0),
                int(row.get("line_num") or 0),
            )
            grouped[key].append(row)

    lines: list[SourceLine] = []
    for line_number, (_, words) in enumerate(sorted(grouped.items()), start=1):
        text = " ".join((word.get("text") or "").strip() for word in words).strip()
        confidences = [Decimal(word.get("conf") or "0") for word in words]
        left = min(int(word.get("left") or 0) for word in words)
        top = min(int(word.get("top") or 0) for word in words)
        right = max(int(word.get("left") or 0) + int(word.get("width") or 0) for word in words)
        bottom = max(int(word.get("top") or 0) + int(word.get("height") or 0) for word in words)
        confidence = (sum(confidences) / Decimal(len(confidences)) / Decimal("100")).quantize(
            Decimal("0.001")
        )
        lines.append(
            SourceLine(
                page=page_number,
                text=text,
                locator=(
                    f"page={page_number};bbox={left},{top},{right},{bottom};ocr_line={line_number}"
                ),
                confidence=max(Decimal("0"), min(Decimal("1"), confidence)),
            )
        )
    return tuple(lines)


@lru_cache(maxsize=32)
def _visual_lines(content: bytes, profile: VisualExtractionProfile) -> tuple[SourceLine, ...]:
    with TemporaryDirectory(prefix="sodif-render-") as temporary:
        directory = Path(temporary)
        images = (
            _mupdf_render(content, directory, profile.dpi)
            if profile.renderer == "mupdf"
            else _poppler_render(content, directory, profile.dpi)
        )
        return tuple(
            line
            for page_number, image in enumerate(images, start=1)
            for line in _ocr_lines(image, page_number, profile)
        )


class PyPdfStructuralAdapter:
    adapter_id = "pypdf-structural-v1"
    view_kind = ViewKind.STRUCTURAL
    cost_units = 1

    def extract(
        self,
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
    ) -> SemanticView:
        lines = _structural_lines(content)
        representation_digest = sha256_digest(
            {
                "adapter": self.adapter_id,
                "revision": document.revision_digest,
                "lines": tuple(
                    (line.page, line.text, line.locator, line.confidence) for line in lines
                ),
            }
        )
        return SemanticView(
            view_id=f"view-{self.view_kind.value}-{representation_digest[7:19]}",
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            kind=self.view_kind,
            adapter_id=self.adapter_id,
            adapter_version="v1",
            fields=extract_schema_fields(
                lines,
                schema,
                view_kind=self.view_kind,
                adapter_id=self.adapter_id,
                adapter_version="v1",
                representation_digest=representation_digest,
            ),
        )


class _VisualAdapter:
    cost_units = 3

    def __init__(self, profile: VisualExtractionProfile, view_kind: ViewKind) -> None:
        if view_kind not in {ViewKind.VISUAL, ViewKind.VISUAL_SECONDARY}:
            raise ValueError("visual PDF adapter requires a visual view kind")
        self.profile = profile
        self.view_kind = view_kind
        self.adapter_id = profile.profile_id

    def extract(
        self,
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
    ) -> SemanticView:
        lines = _visual_lines(content, self.profile)
        representation_digest = sha256_digest(
            {
                "adapter": self.adapter_id,
                "revision": document.revision_digest,
                "content_digest": sha256_bytes(content),
                "lines": tuple(
                    (line.page, line.text, line.locator, line.confidence) for line in lines
                ),
            }
        )
        return SemanticView(
            view_id=f"view-{self.view_kind.value}-{representation_digest[7:19]}",
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            kind=self.view_kind,
            adapter_id=self.adapter_id,
            adapter_version="v1",
            fields=extract_schema_fields(
                lines,
                schema,
                view_kind=self.view_kind,
                adapter_id=self.adapter_id,
                adapter_version="v1",
                representation_digest=representation_digest,
            ),
        )


class PyMuPDFTesseractAdapter(_VisualAdapter):
    def __init__(self, profile: VisualExtractionProfile, view_kind: ViewKind) -> None:
        if profile.renderer != "mupdf":
            raise ValueError("MuPDF adapter requires a mupdf profile")
        super().__init__(profile, view_kind)


class PopplerTesseractAdapter(_VisualAdapter):
    def __init__(self, profile: VisualExtractionProfile, view_kind: ViewKind) -> None:
        if profile.renderer != "poppler":
            raise ValueError("Poppler adapter requires a poppler profile")
        super().__init__(profile, view_kind)


def challenged_pdf_adapters(
    challenge: SemanticChallenge,
) -> tuple[PyPdfStructuralAdapter, _VisualAdapter, _VisualAdapter]:
    if challenge.selected_profiles[0] != PyPdfStructuralAdapter.adapter_id:
        raise DocumentExtractionError("challenge does not select the structural PDF profile")
    visual_adapters: list[_VisualAdapter] = []
    for index, profile_id in enumerate(challenge.selected_profiles[1:3]):
        try:
            profile = VISUAL_PROFILES[profile_id]
        except KeyError as exc:
            raise DocumentExtractionError(f"unknown challenge profile: {profile_id}") from exc
        kind = ViewKind.VISUAL if index == 0 else ViewKind.VISUAL_SECONDARY
        adapter_type = (
            PyMuPDFTesseractAdapter if profile.renderer == "mupdf" else PopplerTesseractAdapter
        )
        visual_adapters.append(adapter_type(profile, kind))
    return PyPdfStructuralAdapter(), visual_adapters[0], visual_adapters[1]
