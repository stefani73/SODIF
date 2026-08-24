"""Tests for versioned intent schema validation."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from sodif.domain.enums import SemanticDataType
from sodif.domain.models import IntentManifest, IntentValue, PolicyReference
from sodif.domain.schemas import (
    IntentFieldDefinition,
    IntentSchema,
    ManifestValidationResult,
    SchemaViolation,
    validate_manifest,
)


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def schema(optional_currency: bool = False) -> IntentSchema:
    return IntentSchema(
        schema_id="purchase-order",
        version="v1",
        action_type="create-purchase-order",
        fields=(
            IntentFieldDefinition(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                description="Supplier identifier",
            ),
            IntentFieldDefinition(
                name="total_amount",
                data_type=SemanticDataType.DECIMAL,
                description="Approved total",
            ),
            IntentFieldDefinition(
                name="currency",
                data_type=SemanticDataType.CURRENCY,
                required=not optional_currency,
                critical=False,
                description="ISO currency code",
            ),
        ),
    )


def value(name: str, data_type: SemanticDataType, content: str | Decimal) -> IntentValue:
    return IntentValue(
        name=name,
        data_type=data_type,
        value=content,
        source_views=("view-a", "view-b"),
        provenance_digests=(digest("c"), digest("d")),
    )


def manifest(fields: tuple[IntentValue, ...], **overrides: str) -> IntentManifest:
    data = {
        "manifest_id": "manifest-001",
        "document_id": "doc-po-001",
        "revision_digest": digest("a"),
        "schema_id": "purchase-order",
        "schema_version": "v1",
        "action_type": "create-purchase-order",
        "policy": PolicyReference(
            policy_id="policy-core",
            version="v1",
            digest=digest("b"),
        ),
        "fields": fields,
    }
    data.update(overrides)
    return IntentManifest.model_validate(data)


def complete_fields() -> tuple[IntentValue, ...]:
    return (
        value("supplier_id", SemanticDataType.IDENTIFIER, "supplier-01"),
        value("total_amount", SemanticDataType.DECIMAL, Decimal("1250.00")),
        value("currency", SemanticDataType.CURRENCY, "EUR"),
    )


def test_complete_manifest_matches_schema() -> None:
    result = validate_manifest(manifest(complete_fields()), schema())

    assert result.valid is True
    assert result.violations == ()


def test_all_shape_violations_are_reported_deterministically() -> None:
    fields = (
        value("total_amount", SemanticDataType.TEXT, "wrong-type"),
        value("unexpected", SemanticDataType.TEXT, "extra"),
    )
    result = validate_manifest(
        manifest(
            fields,
            schema_id="different-schema",
            schema_version="v2",
            action_type="different-action",
        ),
        schema(),
    )

    assert result.valid is False
    assert [violation.code for violation in result.violations] == [
        "schema_id_mismatch",
        "schema_version_mismatch",
        "action_type_mismatch",
        "required_field_missing",
        "field_type_mismatch",
        "required_field_missing",
        "unknown_field",
    ]


def test_optional_field_can_be_absent() -> None:
    fields = (
        value("supplier_id", SemanticDataType.IDENTIFIER, "supplier-01"),
        value("total_amount", SemanticDataType.DECIMAL, Decimal("1250.00")),
    )

    assert validate_manifest(manifest(fields), schema(optional_currency=True)).valid is True


def test_schema_and_validation_result_invariants_are_enforced() -> None:
    duplicate = IntentFieldDefinition(
        name="supplier_id",
        data_type=SemanticDataType.IDENTIFIER,
        description="Supplier",
    )
    with pytest.raises(ValidationError, match="field names"):
        IntentSchema(
            schema_id="purchase-order",
            version="v1",
            action_type="create-purchase-order",
            fields=(duplicate, duplicate),
        )
    with pytest.raises(ValidationError, match="critical field"):
        IntentSchema(
            schema_id="purchase-order",
            version="v1",
            action_type="create-purchase-order",
            fields=(
                IntentFieldDefinition(
                    name="note",
                    data_type=SemanticDataType.TEXT,
                    critical=False,
                    description="Optional note",
                ),
            ),
        )
    violation = SchemaViolation(code="invalid-shape", message="invalid")
    with pytest.raises(ValidationError, match="valid must"):
        ManifestValidationResult(valid=True, violations=(violation,))
    with pytest.raises(ValidationError, match="valid must"):
        ManifestValidationResult(valid=False)
