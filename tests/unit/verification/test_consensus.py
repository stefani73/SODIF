"""Consensus tests across independent structural, visual and target views."""

from decimal import Decimal

import pytest

from sodif.domain.enums import ConsensusStatus, SemanticDataType, ViewKind
from sodif.domain.models import FieldProvenance, SemanticField, SemanticView
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema
from sodif.domain.types import JsonScalar
from sodif.verification.consensus import ConsensusPolicy, DeterministicConsensusEngine
from sodif.verification.errors import VerificationInputError


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def schema() -> IntentSchema:
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
                required=False,
                critical=False,
                description="ISO currency",
            ),
        ),
    )


def view(
    kind: ViewKind,
    values: dict[str, tuple[SemanticDataType, JsonScalar, Decimal]],
    *,
    document_id: str = "doc-001",
) -> SemanticView:
    adapter_id = f"adapter-{kind.value}"
    character = {ViewKind.STRUCTURAL: "a", ViewKind.VISUAL: "b", ViewKind.TARGET: "c"}[kind]
    fields = tuple(
        SemanticField(
            name=name,
            data_type=data_type,
            value=value,
            confidence=confidence,
            provenance=FieldProvenance(
                view_kind=kind,
                adapter_id=adapter_id,
                adapter_version="v1",
                locator=f"{kind.value}:{name}",
                source_digest=digest(character),
            ),
        )
        for name, (data_type, value, confidence) in values.items()
    )
    return SemanticView(
        view_id=f"view-{kind.value}",
        document_id=document_id,
        revision_digest=digest("d"),
        kind=kind,
        adapter_id=adapter_id,
        adapter_version="v1",
        fields=fields,
    )


def complete_values(amount: JsonScalar, currency: str = "EUR") -> dict[
    str, tuple[SemanticDataType, JsonScalar, Decimal]
]:
    return {
        "supplier_id": (SemanticDataType.IDENTIFIER, "SUP-01", Decimal("0.98")),
        "total_amount": (SemanticDataType.DECIMAL, amount, Decimal("0.97")),
        "currency": (SemanticDataType.CURRENCY, currency, Decimal("0.96")),
    }


def test_equivalent_representations_reach_typed_consensus() -> None:
    engine = DeterministicConsensusEngine()
    result = engine.evaluate(
        (
            view(ViewKind.STRUCTURAL, complete_values(Decimal("1250.00"), "EUR")),
            view(ViewKind.VISUAL, complete_values("1250,00", "eur")),
        ),
        schema(),
    )

    fields = {field.name: field for field in result.fields}
    assert result.status is ConsensusStatus.ACCEPTED
    assert fields["total_amount"].accepted_value == Decimal("1.25E+3")
    assert fields["currency"].accepted_value == "EUR"
    assert len(fields["supplier_id"].supporting_views) == 2


def test_critical_disagreement_is_not_overruled_by_a_majority() -> None:
    result = DeterministicConsensusEngine().evaluate(
        (
            view(ViewKind.STRUCTURAL, complete_values(Decimal("100"))),
            view(ViewKind.VISUAL, complete_values(Decimal("200"))),
            view(ViewKind.TARGET, complete_values(Decimal("100"))),
        ),
        schema(),
    )

    amount = next(field for field in result.fields if field.name == "total_amount")
    assert result.status is ConsensusStatus.CONFLICT
    assert amount.status is ConsensusStatus.CONFLICT
    assert len(amount.candidates) == 3


def test_noncritical_field_can_use_a_unique_majority() -> None:
    result = DeterministicConsensusEngine().evaluate(
        (
            view(ViewKind.STRUCTURAL, complete_values(100, "EUR")),
            view(ViewKind.VISUAL, complete_values(100, "USD")),
            view(ViewKind.TARGET, complete_values(100, "EUR")),
        ),
        schema(),
    )

    currency = next(field for field in result.fields if field.name == "currency")
    assert result.status is ConsensusStatus.ACCEPTED
    assert currency.accepted_value == "EUR"
    assert len(currency.supporting_views) == 2


def test_missing_or_low_confidence_evidence_remains_fail_closed() -> None:
    structural = complete_values(100)
    visual = complete_values(100)
    visual["total_amount"] = (SemanticDataType.DECIMAL, 100, Decimal("0.50"))
    structural.pop("currency")
    visual.pop("currency")

    result = DeterministicConsensusEngine().evaluate(
        (view(ViewKind.STRUCTURAL, structural), view(ViewKind.VISUAL, visual)),
        schema(),
    )

    fields = {field.name: field for field in result.fields}
    assert result.status is ConsensusStatus.MISSING
    assert fields["total_amount"].status is ConsensusStatus.MISSING
    assert "currency" not in fields


def test_mismatched_or_dependent_views_are_rejected() -> None:
    structural = view(ViewKind.STRUCTURAL, complete_values(100))
    other_document = view(ViewKind.VISUAL, complete_values(100), document_id="doc-002")
    duplicate = structural.model_copy(update={"view_id": "view-copy"})
    engine = DeterministicConsensusEngine()

    with pytest.raises(VerificationInputError, match="same signed revision"):
        engine.evaluate((structural, other_document), schema())
    with pytest.raises(VerificationInputError, match="independent"):
        engine.evaluate((structural, duplicate), schema())
    with pytest.raises(VerificationInputError, match="requires semantic views"):
        engine.evaluate((), schema())


def test_consensus_policy_rejects_unsafe_thresholds() -> None:
    with pytest.raises(ValueError, match="at least two"):
        ConsensusPolicy(minimum_independent_views=1)
    with pytest.raises(ValueError, match="between"):
        ConsensusPolicy(minimum_confidence=Decimal("1.1"))
