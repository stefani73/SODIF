"""Tests for post-signature challenges and execution-bound field proofs."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from sodif.demo.fixtures import BASE_PDF, flight_policy
from sodif.domain.canonical import sha256_bytes
from sodif.domain.enums import DocumentFormat, HttpMethod, ParameterLocation, SignatureStatus
from sodif.domain.models import ActionParameter, DocumentEnvelope, ExecutionPlan, SignatureEvidence
from sodif.invariance import (
    ChallengePolicy,
    ExecutionProofService,
    InvarianceRejected,
    InvarianceRejectionCode,
    SemanticChallengeGenerator,
)
from sodif.invariance.sample import sample_execution_proof


def document() -> DocumentEnvelope:
    return DocumentEnvelope(
        document_id="doc-proof-001",
        format=DocumentFormat.PDF,
        revision_digest=sha256_bytes(BASE_PDF),
        signatures=(
            SignatureEvidence(
                signer_id="signer-01",
                status=SignatureStatus.VALID,
                covers_revision=True,
                validated_at=datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
                validator_id="validator-01",
                validator_version="v1",
            ),
        ),
        policy=flight_policy(),
        ingested_at=datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
    )


def plan() -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="plan-proof-001",
        intent_digest=f"sha256:{'d' * 64}",
        method=HttpMethod.POST,
        path="/purchase-orders",
        audience="erp-api",
        parameters=(
            ActionParameter(
                name="supplier_id",
                location=ParameterLocation.BODY,
                value="SUP-01",
            ),
            ActionParameter(
                name="total_amount",
                location=ParameterLocation.BODY,
                value=Decimal("1250.00"),
            ),
        ),
    )


def test_challenge_is_post_signature_deterministic_and_nonce_sensitive() -> None:
    generator = SemanticChallengeGenerator()

    first = generator.generate(document(), bytes(range(32)))
    repeated = generator.generate(document(), bytes(range(32)))
    changed = generator.generate(document(), bytes(range(1, 33)))

    assert first == repeated
    assert first.challenge_digest != changed.challenge_digest
    assert first.selected_profiles[0] == "pypdf-structural-v1"
    assert set(first.selected_profiles[1:]) == {
        "mupdf-tesseract-300-psm6-v1",
        "poppler-tesseract-360-psm11-v1",
    }
    with pytest.raises(ValueError, match="128 bits"):
        generator.generate(document(), b"short")
    with pytest.raises(ValueError, match="unique"):
        ChallengePolicy(visual_profiles=("same", "same"))


def test_execution_proof_covers_every_parameter_and_detects_changes() -> None:
    approved_plan = plan()
    bundle = sample_execution_proof(
        approved_plan,
        document_id="doc-proof-001",
        revision_digest=document().revision_digest,
        policy_digest=document().policy.digest,
    )
    service = ExecutionProofService()

    service.verify(bundle, approved_plan)
    assert {binding.parameter_name for binding in bundle.bindings} == {
        "supplier_id",
        "total_amount",
    }
    changed_plan = approved_plan.model_copy(update={"path": "/other-orders"})
    with pytest.raises(InvarianceRejected) as changed:
        service.verify(bundle, changed_plan)
    assert changed.value.code is InvarianceRejectionCode.ACTION_MISMATCH

    extra_parameter = ActionParameter(
        name="cost_center",
        location=ParameterLocation.BODY,
        value="CC-01",
    )
    expanded_plan = approved_plan.model_copy(
        update={"parameters": (*approved_plan.parameters, extra_parameter)}
    )
    with pytest.raises(InvarianceRejected) as uncovered:
        service.bind(bundle.invariance, expanded_plan)
    assert uncovered.value.code is InvarianceRejectionCode.PAYLOAD_COVERAGE_MISSING


def test_modified_field_commitment_or_binding_is_rejected() -> None:
    approved_plan = plan()
    bundle = sample_execution_proof(approved_plan)
    service = ExecutionProofService()
    changed_field = bundle.invariance.fields[0].model_copy(update={"value": "SUP-99"})
    changed_invariance = bundle.invariance.model_copy(
        update={"fields": (changed_field, *bundle.invariance.fields[1:])}
    )
    changed_bundle = bundle.model_copy(update={"invariance": changed_invariance})

    with pytest.raises(InvarianceRejected) as field_change:
        service.verify(changed_bundle, approved_plan)
    assert field_change.value.code is InvarianceRejectionCode.FIELD_ROOT_MISMATCH

    duplicate = bundle.bindings[0]
    with pytest.raises(ValidationError, match="unique"):
        bundle.model_copy(update={"bindings": (duplicate, duplicate)}).model_validate(
            bundle.model_copy(update={"bindings": (duplicate, duplicate)}).model_dump()
        )
