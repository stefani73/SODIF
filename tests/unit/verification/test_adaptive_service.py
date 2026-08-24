"""Adaptive routing tests proving bounded cost and fail-closed escalation."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from sodif.domain.enums import (
    ConsensusStatus,
    DocumentFormat,
    HttpMethod,
    SemanticDataType,
    SignatureStatus,
    VerificationLevel,
    VerificationOutcomeStatus,
    ViewKind,
)
from sodif.domain.models import (
    ActionContext,
    DocumentEnvelope,
    FieldProvenance,
    PolicyReference,
    SemanticField,
    SemanticView,
    SignatureEvidence,
)
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema
from sodif.domain.types import JsonScalar
from sodif.verification.consensus import DeterministicConsensusEngine
from sodif.verification.errors import VerificationInputError
from sodif.verification.risk import AdaptiveRiskPolicy
from sodif.verification.service import AdaptiveVerificationService

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def active_policy() -> PolicyReference:
    return PolicyReference(policy_id="policy-01", version="v1", digest=digest("b"))


def document(status: SignatureStatus = SignatureStatus.VALID) -> DocumentEnvelope:
    return DocumentEnvelope(
        document_id="doc-001",
        format=DocumentFormat.PDF,
        revision_digest=digest("a"),
        signatures=(
            SignatureEvidence(
                signer_id="signer-01",
                status=status,
                covers_revision=True,
                validated_at=NOW,
                validator_id="validator-01",
                validator_version="v1",
            ),
        ),
        policy=active_policy(),
        ingested_at=NOW,
    )


def schema() -> IntentSchema:
    return IntentSchema(
        schema_id="purchase-order",
        version="v1",
        action_type="create-purchase-order",
        fields=(
            IntentFieldDefinition(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                description="Supplier",
            ),
            IntentFieldDefinition(
                name="total_amount",
                data_type=SemanticDataType.DECIMAL,
                description="Approved total",
            ),
        ),
    )


def action(method: HttpMethod = HttpMethod.POST) -> ActionContext:
    return ActionContext(
        action_type="create-purchase-order",
        method=method,
        path="/purchase-orders",
        audience="erp-api",
    )


class FakeAdapter:
    def __init__(
        self,
        view_kind: ViewKind,
        cost_units: int,
        values: dict[str, tuple[SemanticDataType, JsonScalar]],
        *,
        wrong_document: bool = False,
    ) -> None:
        self._view_kind = view_kind
        self._cost_units = cost_units
        self.values = values
        self.wrong_document = wrong_document
        self.calls = 0

    @property
    def adapter_id(self) -> str:
        return f"adapter-{self._view_kind.value}"

    @property
    def view_kind(self) -> ViewKind:
        return self._view_kind

    @property
    def cost_units(self) -> int:
        return self._cost_units

    def extract(
        self,
        source_document: DocumentEnvelope,
        content: bytes,
        intent_schema: IntentSchema,
    ) -> SemanticView:
        del content, intent_schema
        self.calls += 1
        digest_character = {
            ViewKind.STRUCTURAL: "a",
            ViewKind.VISUAL: "b",
            ViewKind.TARGET: "c",
        }[self.view_kind]
        fields = tuple(
            SemanticField(
                name=name,
                data_type=data_type,
                value=value,
                confidence=Decimal("0.95"),
                provenance=FieldProvenance(
                    view_kind=self.view_kind,
                    adapter_id=self.adapter_id,
                    adapter_version="v1",
                    locator=f"{self.view_kind.value}:{name}",
                    source_digest=digest(digest_character),
                ),
            )
            for name, (data_type, value) in self.values.items()
        )
        return SemanticView(
            view_id=f"view-{self.view_kind.value}",
            document_id="doc-wrong" if self.wrong_document else source_document.document_id,
            revision_digest=source_document.revision_digest,
            kind=self.view_kind,
            adapter_id=self.adapter_id,
            adapter_version="v1",
            fields=fields,
        )


def values(amount: JsonScalar = Decimal("100")) -> dict[
    str, tuple[SemanticDataType, JsonScalar]
]:
    return {
        "supplier_id": (SemanticDataType.IDENTIFIER, "SUP-01"),
        "total_amount": (SemanticDataType.DECIMAL, amount),
    }


def adapters(
    structural_values: dict[str, tuple[SemanticDataType, JsonScalar]] | None = None,
    visual_values: dict[str, tuple[SemanticDataType, JsonScalar]] | None = None,
    target_values: dict[str, tuple[SemanticDataType, JsonScalar]] | None = None,
) -> tuple[FakeAdapter, FakeAdapter, FakeAdapter]:
    return (
        FakeAdapter(ViewKind.STRUCTURAL, 1, structural_values or values()),
        FakeAdapter(ViewKind.VISUAL, 3, visual_values or values()),
        FakeAdapter(ViewKind.TARGET, 2, target_values or values()),
    )


def service(adapter_set: tuple[FakeAdapter, ...]) -> AdaptiveVerificationService:
    return AdaptiveVerificationService(
        AdaptiveRiskPolicy(active_policy()),
        DeterministicConsensusEngine(),
        adapter_set,
    )


def test_low_risk_consensus_stops_before_the_third_adapter() -> None:
    adapter_set = adapters()
    outcome = service(adapter_set).verify(document(), b"pdf", schema(), action())

    assert outcome.status is VerificationOutcomeStatus.ACCEPTED
    assert outcome.initial_level is VerificationLevel.V1_TARGETED
    assert outcome.total_cost_units == 4
    assert outcome.saved_cost_units == 2
    assert len(outcome.attempts) == 1
    assert adapter_set[2].calls == 0


def test_missing_evidence_triggers_one_bounded_additional_path() -> None:
    visual: dict[str, tuple[SemanticDataType, JsonScalar]] = {
        "supplier_id": (SemanticDataType.IDENTIFIER, "SUP-01")
    }
    adapter_set = adapters(visual_values=visual)

    outcome = service(adapter_set).verify(document(), b"pdf", schema(), action())

    assert outcome.status is VerificationOutcomeStatus.ACCEPTED
    assert outcome.initial_level is VerificationLevel.V1_TARGETED
    assert outcome.final_level is VerificationLevel.V2_EXTENDED
    assert outcome.total_cost_units == outcome.available_cost_units == 6
    assert len(outcome.attempts) == 2
    assert adapter_set[2].calls == 1


def test_critical_conflict_remains_escalated_after_full_route() -> None:
    adapter_set = adapters(
        visual_values=values(Decimal("200")),
        target_values=values(Decimal("100")),
    )

    outcome = service(adapter_set).verify(document(), b"pdf", schema(), action())

    assert outcome.status is VerificationOutcomeStatus.ESCALATED
    assert outcome.reasons == ("semantic-conflict",)
    assert outcome.final_consensus is not None
    assert outcome.final_consensus.status is ConsensusStatus.CONFLICT
    assert len(outcome.attempts) == 2


def test_high_risk_action_runs_extended_route_but_still_requires_review() -> None:
    adapter_set = adapters()

    outcome = service(adapter_set).verify(
        document(),
        b"pdf",
        schema(),
        action(HttpMethod.DELETE),
    )

    assert outcome.status is VerificationOutcomeStatus.ESCALATED
    assert outcome.initial_level is VerificationLevel.V3_REVIEW
    assert outcome.reasons == ("risk-review-required",)
    assert len(outcome.attempts) == 1
    assert [adapter.calls for adapter in adapter_set] == [1, 1, 1]


def test_invalid_signed_revision_blocks_all_semantic_cost() -> None:
    adapter_set = adapters()

    outcome = service(adapter_set).verify(
        document(SignatureStatus.INVALID),
        b"pdf",
        schema(),
        action(),
    )

    assert outcome.status is VerificationOutcomeStatus.BLOCKED
    assert outcome.total_cost_units == 0
    assert outcome.attempts == ()
    assert [adapter.calls for adapter in adapter_set] == [0, 0, 0]


def test_adapter_identity_mismatch_is_rejected() -> None:
    adapter_set = adapters()
    adapter_set = (
        FakeAdapter(ViewKind.STRUCTURAL, 1, values(), wrong_document=True),
        adapter_set[1],
        adapter_set[2],
    )

    with pytest.raises(VerificationInputError, match="another revision"):
        service(adapter_set).verify(document(), b"pdf", schema(), action())
