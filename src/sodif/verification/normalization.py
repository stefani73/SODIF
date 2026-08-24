"""Deterministic normalization used only to compare semantic representations."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from unicodedata import normalize

from sodif.domain.enums import SemanticDataType
from sodif.domain.types import JsonScalar
from sodif.verification.errors import SemanticNormalizationError

_CURRENCY = re.compile(r"^[A-Z]{3}$")
_INTEGER = re.compile(r"^[+-]?\d+$")


@dataclass(frozen=True, slots=True)
class NormalizedSemanticValue:
    canonical_value: JsonScalar
    comparison_key: str


def _clean_text(value: object) -> str:
    if not isinstance(value, str):
        raise SemanticNormalizationError("value must be text")
    cleaned = " ".join(normalize("NFKC", value).split())
    if not cleaned:
        raise SemanticNormalizationError("text value cannot be empty")
    return cleaned


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise SemanticNormalizationError("boolean or null is not a decimal")
    source = str(value).strip()
    if "," in source:
        if "." in source or source.count(",") != 1:
            raise SemanticNormalizationError("ambiguous decimal separators")
        source = source.replace(",", ".")
    try:
        result = Decimal(source)
    except InvalidOperation as exc:
        raise SemanticNormalizationError("invalid decimal value") from exc
    if not result.is_finite():
        raise SemanticNormalizationError("decimal value must be finite")
    return result.normalize() if result else Decimal("0")


def normalize_semantic_value(
    data_type: SemanticDataType,
    value: object,
) -> NormalizedSemanticValue:
    """Return an exact output value and a stable equivalence key."""
    if data_type is SemanticDataType.TEXT:
        cleaned = _clean_text(value)
        return NormalizedSemanticValue(cleaned, f"text:{cleaned.casefold()}")
    if data_type is SemanticDataType.IDENTIFIER:
        cleaned = _clean_text(value)
        return NormalizedSemanticValue(cleaned, f"identifier:{cleaned}")
    if data_type is SemanticDataType.CURRENCY:
        currency = _clean_text(value).upper()
        if _CURRENCY.fullmatch(currency) is None:
            raise SemanticNormalizationError("currency must be a three-letter ISO-like code")
        return NormalizedSemanticValue(currency, f"currency:{currency}")
    if data_type is SemanticDataType.INTEGER:
        if isinstance(value, bool):
            raise SemanticNormalizationError("boolean is not an integer")
        if isinstance(value, int):
            integer = value
        elif isinstance(value, str) and _INTEGER.fullmatch(value.strip()):
            integer = int(value)
        else:
            raise SemanticNormalizationError("invalid integer value")
        return NormalizedSemanticValue(integer, f"integer:{integer}")
    if data_type is SemanticDataType.DECIMAL:
        decimal = _decimal(value)
        return NormalizedSemanticValue(decimal, f"decimal:{decimal}")
    if data_type is SemanticDataType.DATE:
        source = _clean_text(value)
        try:
            parsed = date.fromisoformat(source)
        except ValueError as exc:
            raise SemanticNormalizationError("date must use ISO 8601 YYYY-MM-DD") from exc
        canonical = parsed.isoformat()
        return NormalizedSemanticValue(canonical, f"date:{canonical}")
    if data_type is SemanticDataType.BOOLEAN:
        if isinstance(value, bool):
            boolean = value
        elif isinstance(value, str) and value.strip().casefold() in {"true", "yes", "da", "1"}:
            boolean = True
        elif isinstance(value, str) and value.strip().casefold() in {"false", "no", "nu", "0"}:
            boolean = False
        else:
            raise SemanticNormalizationError("invalid boolean value")
        return NormalizedSemanticValue(boolean, f"boolean:{str(boolean).lower()}")
    raise SemanticNormalizationError(f"unsupported semantic type: {data_type}")
