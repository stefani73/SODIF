"""Schema-driven field extraction from page-aware text lines."""

import re
from dataclasses import dataclass
from decimal import Decimal

from sodif.domain.canonical import sha256_digest
from sodif.domain.enums import SemanticDataType, ViewKind
from sodif.domain.models import FieldProvenance, SemanticField
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema


@dataclass(frozen=True, slots=True)
class SourceLine:
    page: int
    text: str
    locator: str
    confidence: Decimal


_VALUE_PATTERNS: dict[SemanticDataType, str] = {
    SemanticDataType.DECIMAL: r"[-+]?[0-9][0-9 .,'`]*",
    SemanticDataType.INTEGER: r"[-+]?[0-9]+",
    SemanticDataType.CURRENCY: r"[A-Za-z]{3}",
    SemanticDataType.DATE: r"[0-9]{1,4}[-./][0-9]{1,2}[-./][0-9]{1,4}",
    SemanticDataType.IDENTIFIER: r"[A-Za-z0-9][A-Za-z0-9._/-]*",
    SemanticDataType.BOOLEAN: r"(?:true|false|yes|no|da|nu|0|1)",
    SemanticDataType.TEXT: r".+",
}


def _label_pattern(name: str) -> str:
    parts = tuple(item for item in re.split(r"[_\s-]+", name) if item)
    return r"[\s_-]*".join(re.escape(item) for item in parts)


def _extract_value(line: str, definition: IntentFieldDefinition) -> str | None:
    pattern = re.compile(
        rf"\b{_label_pattern(definition.name)}\b[ \t]*[:=][ \t]*"
        rf"(?P<value>{_VALUE_PATTERNS[definition.data_type]})",
        flags=re.IGNORECASE,
    )
    match = pattern.search(line)
    if match is None:
        return None
    return match.group("value").strip().rstrip(";,.")


def extract_schema_fields(
    lines: tuple[SourceLine, ...],
    schema: IntentSchema,
    *,
    view_kind: ViewKind,
    adapter_id: str,
    adapter_version: str,
    representation_digest: str,
) -> tuple[SemanticField, ...]:
    fields: list[SemanticField] = []
    for definition in schema.fields:
        candidates = [
            (line, value)
            for line in lines
            if (value := _extract_value(line.text, definition)) is not None
        ]
        if not candidates:
            continue
        selected, value = sorted(
            candidates,
            key=lambda item: (-item[0].confidence, item[0].page, item[0].locator),
        )[0]
        fields.append(
            SemanticField(
                name=definition.name,
                data_type=definition.data_type,
                value=value,
                raw_value=value,
                confidence=selected.confidence,
                provenance=FieldProvenance(
                    view_kind=view_kind,
                    adapter_id=adapter_id,
                    adapter_version=adapter_version,
                    locator=selected.locator,
                    source_digest=sha256_digest(
                        {
                            "representation_digest": representation_digest,
                            "field": definition.name,
                            "page": selected.page,
                            "locator": selected.locator,
                            "raw_value": value,
                        }
                    ),
                ),
            )
        )
    return tuple(fields)
