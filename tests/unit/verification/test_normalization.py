"""Deterministic semantic normalization tests."""

from decimal import Decimal

import pytest

from sodif.domain.enums import SemanticDataType
from sodif.verification.errors import SemanticNormalizationError
from sodif.verification.normalization import normalize_semantic_value


def test_text_identifier_and_currency_normalization_are_explicit() -> None:
    text = normalize_semantic_value(SemanticDataType.TEXT, "  ACME\u00a0  S.R.L. ")
    identifier = normalize_semantic_value(SemanticDataType.IDENTIFIER, " SUP-01 ")
    currency = normalize_semantic_value(SemanticDataType.CURRENCY, " eur ")

    assert text.canonical_value == "ACME S.R.L."
    assert text.comparison_key == "text:acme s.r.l."
    assert identifier.comparison_key == "identifier:SUP-01"
    assert currency.canonical_value == "EUR"


def test_numeric_date_and_boolean_values_receive_canonical_forms() -> None:
    assert normalize_semantic_value(SemanticDataType.INTEGER, "+0042").canonical_value == 42
    assert normalize_semantic_value(SemanticDataType.DECIMAL, "1250,00").canonical_value == Decimal(
        "1.25E+3"
    )
    assert (
        normalize_semantic_value(SemanticDataType.DATE, "2026-08-24").canonical_value
        == "2026-08-24"
    )
    assert normalize_semantic_value(SemanticDataType.BOOLEAN, "da").canonical_value is True
    assert normalize_semantic_value(SemanticDataType.BOOLEAN, False).canonical_value is False


@pytest.mark.parametrize(
    ("data_type", "value"),
    [
        (SemanticDataType.TEXT, "  "),
        (SemanticDataType.IDENTIFIER, 12),
        (SemanticDataType.CURRENCY, "EURO"),
        (SemanticDataType.INTEGER, True),
        (SemanticDataType.INTEGER, "1.2"),
        (SemanticDataType.DECIMAL, "1,250.00"),
        (SemanticDataType.DECIMAL, "NaN"),
        (SemanticDataType.DATE, "24.08.2026"),
        (SemanticDataType.BOOLEAN, "perhaps"),
    ],
)
def test_ambiguous_values_are_rejected(
    data_type: SemanticDataType,
    value: object,
) -> None:
    with pytest.raises(SemanticNormalizationError):
        normalize_semantic_value(data_type, value)
