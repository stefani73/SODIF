"""Intent assembly, action compilation and controlled API execution tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from sodif.domain.canonical import sha256_digest
from sodif.domain.contracts import ActionCompiler, ApiExecutor, IntentAssembler
from sodif.domain.enums import (
    ApiExecutionStatus,
    ConsensusStatus,
    DocumentFormat,
    HttpMethod,
    SemanticDataType,
    SignatureStatus,
)
from sodif.domain.models import (
    ActionContext,
    ActionParameter,
    CandidateValue,
    ConsensusField,
    ConsensusResult,
    DocumentEnvelope,
    ExecutionPlan,
    PolicyReference,
    SignatureEvidence,
)
from sodif.domain.permits import ExecutionAuthorization
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema
from sodif.domain.types import JsonScalar
from sodif.execution import (
    ConsensusIntentAssembler,
    DeterministicActionCompiler,
    ExecutionRejected,
    InMemoryApiExecutor,
)

NOW = datetime(2026, 8, 24, 14, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def policy() -> PolicyReference:
    return PolicyReference(policy_id="policy-01", version="v1", digest=digest("b"))


def document() -> DocumentEnvelope:
    return DocumentEnvelope(
        document_id="doc-001",
        format=DocumentFormat.PDF,
        revision_digest=digest("a"),
        signatures=(
            SignatureEvidence(
                signer_id="signer-01",
                status=SignatureStatus.VALID,
                covers_revision=True,
                validated_at=NOW,
                validator_id="validator-01",
                validator_version="v1",
            ),
        ),
        policy=policy(),
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
                description="Supplier identifier",
            ),
            IntentFieldDefinition(
                name="total_amount",
                data_type=SemanticDataType.DECIMAL,
                description="Approved total",
            ),
        ),
    )


def candidate(view_id: str, value: JsonScalar, character: str) -> CandidateValue:
    return CandidateValue(
        view_id=view_id,
        value=value,
        confidence=Decimal("0.96"),
        provenance_digest=digest(character),
    )


def accepted_consensus() -> ConsensusResult:
    return ConsensusResult(
        document_id="doc-001",
        revision_digest=digest("a"),
        status=ConsensusStatus.ACCEPTED,
        fields=(
            ConsensusField(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                status=ConsensusStatus.ACCEPTED,
                accepted_value="SUP-01",
                candidates=(
                    candidate("view-structural", "SUP-01", "c"),
                    candidate("view-visual", "SUP-01", "d"),
                ),
                supporting_views=("view-structural", "view-visual"),
            ),
            ConsensusField(
                name="total_amount",
                data_type=SemanticDataType.DECIMAL,
                status=ConsensusStatus.ACCEPTED,
                accepted_value=Decimal("1250"),
                candidates=(
                    candidate("view-structural", Decimal("1250"), "e"),
                    candidate("view-visual", Decimal("1250"), "f"),
                ),
                supporting_views=("view-structural", "view-visual"),
            ),
        ),
    )


def target() -> ActionContext:
    return ActionContext(
        action_type="create-purchase-order",
        method=HttpMethod.POST,
        path="/purchase-orders",
        audience="erp-api",
    )


def test_accepted_consensus_builds_deterministic_manifest_and_plan() -> None:
    assembler = ConsensusIntentAssembler()
    compiler = DeterministicActionCompiler()

    first = assembler.assemble(document(), accepted_consensus(), schema(), policy())
    second = assembler.assemble(document(), accepted_consensus(), schema(), policy())
    execution_plan = compiler.compile(first, target())

    assert isinstance(assembler, IntentAssembler)
    assert isinstance(compiler, ActionCompiler)
    assert first == second
    assert execution_plan.intent_digest == sha256_digest(first)
    assert [parameter.name for parameter in execution_plan.parameters] == [
        "supplier_id",
        "total_amount",
    ]


def test_assembler_and_compiler_reject_inconsistent_context() -> None:
    assembler = ConsensusIntentAssembler()
    accepted = accepted_consensus()
    conflict = accepted.model_copy(update={"status": ConsensusStatus.CONFLICT})
    other_document = document().model_copy(update={"document_id": "doc-002"})
    wrong_policy = PolicyReference(policy_id="policy-02", version="v1", digest=digest("c"))

    with pytest.raises(ExecutionRejected, match="accepted"):
        assembler.assemble(document(), conflict, schema(), policy())
    with pytest.raises(ExecutionRejected, match="revision differ"):
        assembler.assemble(other_document, accepted, schema(), policy())
    with pytest.raises(ExecutionRejected, match="policy differ"):
        assembler.assemble(document(), accepted, schema(), wrong_policy)

    manifest = assembler.assemble(document(), accepted, schema(), policy())
    with pytest.raises(ExecutionRejected, match="action_type"):
        DeterministicActionCompiler().compile(
            manifest,
            target().model_copy(update={"action_type": "delete-order"}),
        )


def test_missing_provenance_is_rejected_before_manifest_creation() -> None:
    accepted = accepted_consensus()
    broken_field = accepted.fields[0].model_copy(update={"candidates": ()})
    broken = ConsensusResult(
        document_id=accepted.document_id,
        revision_digest=accepted.revision_digest,
        status=ConsensusStatus.ACCEPTED,
        fields=(broken_field, accepted.fields[1]),
    )

    with pytest.raises(ExecutionRejected, match="lacks provenance"):
        ConsensusIntentAssembler().assemble(document(), broken, schema(), policy())


def test_controlled_api_executor_requires_matching_authorization_once() -> None:
    manifest = ConsensusIntentAssembler().assemble(
        document(), accepted_consensus(), schema(), policy()
    )
    execution_plan = DeterministicActionCompiler().compile(manifest, target())
    authorization = ExecutionAuthorization(
        permit_id="permit-001",
        document_id="doc-001",
        revision_digest=digest("a"),
        action_digest=sha256_digest(execution_plan),
        execution_proof_digest=digest("1"),
        field_root=digest("2"),
        audience="erp-api",
        authorized_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )
    executor = InMemoryApiExecutor(FixedClock())

    receipt = executor.execute(authorization, execution_plan)

    assert isinstance(executor, ApiExecutor)
    assert receipt.status is ApiExecutionStatus.SUCCEEDED
    assert executor.get(receipt.execution_id) == receipt
    with pytest.raises(ExecutionRejected, match="already executed"):
        executor.execute(authorization, execution_plan)


def test_controlled_api_executor_rejects_other_plan_or_audience() -> None:
    execution_plan = ExecutionPlan(
        plan_id="plan-001",
        intent_digest=digest("c"),
        method=HttpMethod.POST,
        path="/purchase-orders",
        audience="erp-api",
        parameters=accepted_plan_parameters(),
    )
    authorization = ExecutionAuthorization(
        permit_id="permit-001",
        document_id="doc-001",
        revision_digest=digest("a"),
        action_digest=sha256_digest(execution_plan),
        execution_proof_digest=digest("1"),
        field_root=digest("2"),
        audience="erp-api",
        authorized_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )
    executor = InMemoryApiExecutor(FixedClock())

    with pytest.raises(ExecutionRejected, match="does not cover"):
        executor.execute(authorization, execution_plan.model_copy(update={"path": "/other"}))
    with pytest.raises(ExecutionRejected, match="audience"):
        executor.execute(
            authorization.model_copy(update={"audience": "other-api"}),
            execution_plan,
        )


def accepted_plan_parameters() -> tuple[ActionParameter, ...]:
    manifest = ConsensusIntentAssembler().assemble(
        document(), accepted_consensus(), schema(), policy()
    )
    return DeterministicActionCompiler().compile(manifest, target()).parameters
