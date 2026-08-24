"""Versioned intent schemas and deterministic manifest validation."""

from typing import Self

from pydantic import Field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import SemanticDataType
from sodif.domain.models import IntentManifest
from sodif.domain.types import FieldName, Identifier


class IntentFieldDefinition(DomainModel):
    name: FieldName
    data_type: SemanticDataType
    required: bool = True
    critical: bool = True
    description: str = Field(min_length=1, max_length=300)


class IntentSchema(DomainModel):
    schema_id: Identifier
    version: Identifier
    action_type: Identifier
    fields: tuple[IntentFieldDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_fields_and_critical_effect(self) -> Self:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("schema field names must be unique")
        if not any(field.critical for field in self.fields):
            raise ValueError("an intent schema requires at least one critical field")
        return self


class SchemaViolation(DomainModel):
    code: Identifier
    field_name: FieldName | None = None
    message: str = Field(min_length=1, max_length=300)


class ManifestValidationResult(DomainModel):
    valid: bool
    violations: tuple[SchemaViolation, ...] = ()

    @model_validator(mode="after")
    def validity_matches_violations(self) -> Self:
        if self.valid == bool(self.violations):
            raise ValueError("valid must be true exactly when violations are empty")
        return self


def validate_manifest(
    manifest: IntentManifest,
    schema: IntentSchema,
) -> ManifestValidationResult:
    """Validate only shape and version; business rules are added in later steps."""
    violations: list[SchemaViolation] = []
    if manifest.schema_id != schema.schema_id:
        violations.append(
            SchemaViolation(code="schema_id_mismatch", message="schema identifiers differ")
        )
    if manifest.schema_version != schema.version:
        violations.append(
            SchemaViolation(code="schema_version_mismatch", message="schema versions differ")
        )
    if manifest.action_type != schema.action_type:
        violations.append(
            SchemaViolation(code="action_type_mismatch", message="action types differ")
        )

    definitions = {field.name: field for field in schema.fields}
    values = {field.name: field for field in manifest.fields}
    for definition in schema.fields:
        value = values.get(definition.name)
        if definition.required and value is None:
            violations.append(
                SchemaViolation(
                    code="required_field_missing",
                    field_name=definition.name,
                    message="required intent field is missing",
                )
            )
        elif value is not None and value.data_type is not definition.data_type:
            violations.append(
                SchemaViolation(
                    code="field_type_mismatch",
                    field_name=definition.name,
                    message="intent field type differs from schema",
                )
            )
    for value in manifest.fields:
        if value.name not in definitions:
            violations.append(
                SchemaViolation(
                    code="unknown_field",
                    field_name=value.name,
                    message="intent field is not declared by schema",
                )
            )
    return ManifestValidationResult(valid=not violations, violations=tuple(violations))
