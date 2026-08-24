"""Deterministic JSON representation and SHA-256 digests."""

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from math import isfinite
from typing import Any

import rfc8785
from pydantic import BaseModel

from sodif.domain.errors import CanonicalizationError
from sodif.domain.types import Digest


def _json_compatible(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_compatible(value.model_dump(mode="json"))
    if isinstance(value, Enum):
        return _json_compatible(value.value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise CanonicalizationError("naive datetimes are not canonicalizable")
        normalized = value.astimezone(UTC).isoformat(timespec="microseconds")
        return normalized.replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float) and not isfinite(value):
        raise CanonicalizationError("non-finite floats are not canonicalizable")
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError("canonical JSON object keys must be strings")
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_compatible(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise CanonicalizationError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return RFC 8785 canonical JSON bytes for supported values."""
    try:
        return rfc8785.dumps(_json_compatible(value))
    except CanonicalizationError:
        raise
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError(str(exc)) from exc


def sha256_digest(value: Any) -> Digest:
    """Digest the canonical representation using an explicit algorithm prefix."""
    return f"sha256:{sha256(canonical_bytes(value)).hexdigest()}"


def sha256_bytes(value: bytes) -> Digest:
    """Digest an immutable binary artifact without JSON transformation."""
    return f"sha256:{sha256(value).hexdigest()}"
