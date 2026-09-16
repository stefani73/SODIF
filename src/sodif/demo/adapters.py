"""Transparent, controlled semantic adapters for reproducible flight scenarios."""

from decimal import Decimal

from sodif.domain.canonical import sha256_digest
from sodif.domain.contracts import SemanticAdapter
from sodif.domain.enums import SemanticDataType, ViewKind
from sodif.domain.models import DocumentEnvelope, FieldProvenance, SemanticField, SemanticView
from sodif.domain.schemas import IntentSchema
from sodif.domain.types import JsonScalar

ScenarioValue = tuple[SemanticDataType, JsonScalar]


class ScenarioSemanticAdapter:
    def __init__(
        self,
        view_kind: ViewKind,
        cost_units: int,
        values: dict[str, ScenarioValue],
        confidence: Decimal = Decimal("0.96"),
    ) -> None:
        if cost_units < 1:
            raise ValueError("scenario adapter cost must be positive")
        self._view_kind = view_kind
        self._cost_units = cost_units
        self._values = dict(values)
        self._confidence = confidence
        self.calls = 0

    @property
    def adapter_id(self) -> str:
        return f"flight-{self._view_kind.value}-adapter"

    @property
    def view_kind(self) -> ViewKind:
        return self._view_kind

    @property
    def cost_units(self) -> int:
        return self._cost_units

    def extract(
        self,
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
    ) -> SemanticView:
        self.calls += 1
        definitions = {field.name: field for field in schema.fields}
        source_digest = sha256_digest(
            {
                "adapter": self.adapter_id,
                "revision": document.revision_digest,
                "content_size": len(content),
                "values": self._values,
            }
        )
        fields = tuple(
            SemanticField(
                name=name,
                data_type=data_type,
                value=value,
                confidence=self._confidence,
                provenance=FieldProvenance(
                    view_kind=self.view_kind,
                    adapter_id=self.adapter_id,
                    adapter_version="v1",
                    locator=f"flight:{self.view_kind.value}:{name}",
                    source_digest=source_digest,
                ),
            )
            for name, (data_type, value) in self._values.items()
            if name in definitions
        )
        if not fields:
            raise ValueError("scenario adapter produced no schema fields")
        return SemanticView(
            view_id=f"view-{self.view_kind.value}",
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            kind=self.view_kind,
            adapter_id=self.adapter_id,
            adapter_version="v1",
            fields=fields,
        )


class FieldMaskingAdapter:
    """Represent an incomplete extraction path without fabricating replacement values."""

    def __init__(self, delegate: SemanticAdapter, omitted_fields: frozenset[str]) -> None:
        self._delegate = delegate
        self._omitted_fields = omitted_fields

    @property
    def adapter_id(self) -> str:
        return self._delegate.adapter_id

    @property
    def view_kind(self) -> ViewKind:
        return self._delegate.view_kind

    @property
    def cost_units(self) -> int:
        return self._delegate.cost_units

    def extract(
        self,
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
    ) -> SemanticView:
        view = self._delegate.extract(document, content, schema)
        return view.model_copy(
            update={
                "fields": tuple(
                    field for field in view.fields if field.name not in self._omitted_fields
                )
            }
        )
