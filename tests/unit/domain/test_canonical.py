"""Tests for canonical representation and cryptographic identity."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import nan

import pytest

from sodif.domain.canonical import canonical_bytes, sha256_digest
from sodif.domain.errors import CanonicalizationError
from sodif.domain.models import PolicyReference


def test_canonical_json_is_independent_of_mapping_order() -> None:
    left = {"z": [3, 2, 1], "a": {"enabled": True, "count": 2}}
    right = {"a": {"count": 2, "enabled": True}, "z": [3, 2, 1]}

    assert canonical_bytes(left) == canonical_bytes(right)
    assert sha256_digest(left) == sha256_digest(right)


def test_dates_decimals_enums_and_models_have_stable_forms() -> None:
    local_time = datetime(2026, 8, 24, 12, 30, tzinfo=timezone(timedelta(hours=3)))
    value = {"when": local_time, "amount": Decimal("10.50")}
    policy = PolicyReference(
        policy_id="policy-core",
        version="v1",
        digest="sha256:" + "a" * 64,
    )

    assert canonical_bytes(value) == b'{"amount":"10.50","when":"2026-08-24T09:30:00.000000Z"}'
    assert canonical_bytes(policy).startswith(b'{"digest":"sha256:')
    assert sha256_digest(policy).startswith("sha256:")
    assert len(sha256_digest(policy)) == 71


@pytest.mark.parametrize(
    "value, message",
    [
        ({1: "not-string"}, "keys must be strings"),
        ({"when": datetime(2026, 8, 24, 9, 0)}, "naive datetimes"),
        ({"value": nan}, "non-finite"),
        ({"unsupported": {"set-value"}}, "unsupported canonical value"),
    ],
)
def test_unsupported_or_ambiguous_values_are_rejected(value: object, message: str) -> None:
    with pytest.raises(CanonicalizationError, match=message):
        canonical_bytes(value)
