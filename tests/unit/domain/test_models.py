"""Invariant tests for immutable SODIF domain contracts."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from sodif.domain.enums import (
    ConsensusStatus,
    DocumentFormat,
    HttpMethod,
    ParameterLocation,
    RiskSeverity,
    SemanticDataType,
    SignatureStatus,
    VerificationLevel,
    ViewKind,
)
from sodif.domain.models import (
    ActionParameter,
    Attribute,
    CandidateValue,
    ConsensusField,
    ConsensusResult,
    DocumentEnvelope,
    EvidenceEvent,
    ExecutionPlan,
    FieldProvenance,
    IntentManifest,
    IntentValue,
    PolicyReference,
    RiskAssessment,
    RiskSignal,
    SemanticField,
    SemanticView,
    SignatureEvidence,
    percentage,
)

NOW = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def digest(character: str = "a") -> str:
    return f"sha256:{character * 64}"


def policy() -> PolicyReference:
    return PolicyReference(policy_id="policy-core", version="v1", digest=digest("b"))


def signature(signer_id: str = "signer-01") -> SignatureEvidence:
    return SignatureEvidence(
        signer_id=signer_id,
        status=SignatureStatus.VALID,
        covers_revision=True,
        validated_at=NOW,
        validator_id="validator-01",
        validator_version="v1",
    )


def provenance(adapter_id: str = "structural-parser") -> FieldProvenance:
    return FieldProvenance(
        view_kind=ViewKind.STRUCTURAL,
        adapter_id=adapter_id,
        adapter_version="v1",
        locator="page:1/table:orders/cell:B4",
        source_digest=digest("c"),
    )


def semantic_field(name: str = "supplier_id") -> SemanticField:
    return SemanticField(
        name=name,
        data_type=SemanticDataType.IDENTIFIER,
        value="supplier-01",
        raw_value="Supplier 01",
        confidence=Decimal("0.99"),
        provenance=provenance(),
    )


def candidate(view_id: str, value: str, character: str) -> CandidateValue:
    return CandidateValue(
        view_id=view_id,
        value=value,
        confidence=Decimal("0.95"),
        provenance_digest=digest(character),
    )


def intent_value(name: str = "supplier_id") -> IntentValue:
    return IntentValue(
        name=name,
        data_type=SemanticDataType.IDENTIFIER,
        value="supplier-01",
        source_views=("view-structural", "view-visual"),
        provenance_digests=(digest("c"), digest("d")),
    )


def test_document_envelope_round_trips_and_is_immutable() -> None:
    envelope = DocumentEnvelope(
        document_id="doc-po-001",
        format=DocumentFormat.PDF,
        revision_digest=digest(),
        signatures=(signature(),),
        policy=policy(),
        ingested_at=NOW,
        attributes=(Attribute(key="tenant-id", value="lab"),),
    )

    restored = DocumentEnvelope.model_validate_json(envelope.model_dump_json())

    assert restored == envelope
    with pytest.raises(ValidationError, match="frozen"):
        envelope.document_id = "doc-po-002"


def test_document_rejects_duplicate_signers_and_attributes() -> None:
    base = {
        "document_id": "doc-po-001",
        "format": DocumentFormat.PDF,
        "revision_digest": digest(),
        "policy": policy(),
        "ingested_at": NOW,
    }

    with pytest.raises(ValidationError, match="signer_id"):
        DocumentEnvelope.model_validate({**base, "signatures": (signature(), signature())})
    with pytest.raises(ValidationError, match="attribute keys"):
        DocumentEnvelope.model_validate(
            {
                **base,
                "signatures": (signature(),),
                "attributes": (
                    Attribute(key="tenant-id", value="a"),
                    Attribute(key="tenant-id", value="b"),
                ),
            }
        )


def test_digest_and_timezone_constraints_fail_closed() -> None:
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        PolicyReference(policy_id="policy-core", version="v1", digest="not-a-digest")
    with pytest.raises(ValidationError, match="timezone_aware"):
        SignatureEvidence(
            signer_id="signer-01",
            status=SignatureStatus.VALID,
            covers_revision=True,
            validated_at=datetime(2026, 8, 24, 9, 0),
            validator_id="validator-01",
            validator_version="v1",
        )


def test_semantic_view_requires_unique_fields() -> None:
    valid = SemanticView(
        view_id="view-structural",
        document_id="doc-po-001",
        revision_digest=digest(),
        adapter_id="structural-parser",
        adapter_version="v1",
        fields=(semantic_field(),),
    )

    assert valid.fields[0].confidence == Decimal("0.99")
    with pytest.raises(ValidationError, match="field names"):
        SemanticView(
            view_id="view-structural",
            document_id="doc-po-001",
            revision_digest=digest(),
            adapter_id="structural-parser",
            adapter_version="v1",
            fields=(semantic_field(), semantic_field()),
        )


def test_consensus_field_invariants_cover_all_states() -> None:
    accepted = ConsensusField(
        name="supplier_id",
        data_type=SemanticDataType.IDENTIFIER,
        status=ConsensusStatus.ACCEPTED,
        accepted_value="supplier-01",
        candidates=(candidate("view-a", "supplier-01", "c"),),
        supporting_views=("view-a",),
    )
    conflict = ConsensusField(
        name="supplier_id",
        data_type=SemanticDataType.IDENTIFIER,
        status=ConsensusStatus.CONFLICT,
        candidates=(
            candidate("view-a", "supplier-01", "c"),
            candidate("view-b", "supplier-02", "d"),
        ),
    )
    missing = ConsensusField(
        name="supplier_id",
        data_type=SemanticDataType.IDENTIFIER,
        status=ConsensusStatus.MISSING,
    )

    assert accepted.accepted_value == "supplier-01"
    assert conflict.status is ConsensusStatus.CONFLICT
    assert missing.candidates == ()

    invalid_cases = (
        {"status": ConsensusStatus.ACCEPTED, "accepted_value": "supplier-01"},
        {"status": ConsensusStatus.CONFLICT, "candidates": (candidate("view-a", "x", "c"),)},
        {
            "status": ConsensusStatus.MISSING,
            "candidates": (candidate("view-a", "x", "c"),),
        },
        {"status": ConsensusStatus.CONFLICT, "accepted_value": "supplier-01"},
        {
            "status": ConsensusStatus.ACCEPTED,
            "accepted_value": "supplier-01",
            "supporting_views": ("view-a", "view-a"),
        },
    )
    for overrides in invalid_cases:
        with pytest.raises(ValidationError):
            ConsensusField(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                **overrides,
            )


def test_consensus_result_derives_global_status_and_unique_fields() -> None:
    accepted = ConsensusField(
        name="supplier_id",
        data_type=SemanticDataType.IDENTIFIER,
        status=ConsensusStatus.ACCEPTED,
        accepted_value="supplier-01",
        supporting_views=("view-a",),
    )
    missing = ConsensusField(
        name="currency",
        data_type=SemanticDataType.CURRENCY,
        status=ConsensusStatus.MISSING,
    )
    result = ConsensusResult(
        document_id="doc-po-001",
        revision_digest=digest(),
        status=ConsensusStatus.MISSING,
        fields=(accepted, missing),
    )

    assert result.status is ConsensusStatus.MISSING
    with pytest.raises(ValidationError, match="global consensus"):
        ConsensusResult(
            document_id="doc-po-001",
            revision_digest=digest(),
            status=ConsensusStatus.ACCEPTED,
            fields=(accepted, missing),
        )
    with pytest.raises(ValidationError, match="field names"):
        ConsensusResult(
            document_id="doc-po-001",
            revision_digest=digest(),
            status=ConsensusStatus.ACCEPTED,
            fields=(accepted, accepted),
        )


def test_manifest_and_execution_plan_reject_ambiguous_components() -> None:
    base_manifest = {
        "manifest_id": "manifest-001",
        "document_id": "doc-po-001",
        "revision_digest": digest(),
        "schema_id": "purchase-order",
        "schema_version": "v1",
        "action_type": "create-purchase-order",
        "policy": policy(),
    }
    manifest = IntentManifest.model_validate({**base_manifest, "fields": (intent_value(),)})

    assert manifest.fields[0].name == "supplier_id"
    with pytest.raises(ValidationError, match="intent field names"):
        IntentManifest.model_validate({**base_manifest, "fields": (intent_value(), intent_value())})

    parameter = ActionParameter(
        name="supplier_id",
        location=ParameterLocation.BODY,
        value="supplier-01",
    )
    plan = ExecutionPlan(
        plan_id="plan-001",
        intent_digest=digest("e"),
        method=HttpMethod.POST,
        path="/purchase-orders",
        audience="erp-purchase-api",
        parameters=(parameter,),
    )

    assert plan.method is HttpMethod.POST
    with pytest.raises(ValidationError, match="parameters"):
        ExecutionPlan(
            plan_id="plan-001",
            intent_digest=digest("e"),
            method=HttpMethod.POST,
            path="/purchase-orders",
            audience="erp-purchase-api",
            parameters=(parameter, parameter),
        )
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        ExecutionPlan(
            plan_id="plan-001",
            intent_digest=digest("e"),
            method=HttpMethod.POST,
            path="/purchase-orders?unsafe=true",
            audience="erp-purchase-api",
            parameters=(parameter,),
        )
    with pytest.raises(ValidationError, match="headers"):
        ExecutionPlan(
            plan_id="plan-001",
            intent_digest=digest("e"),
            method=HttpMethod.POST,
            path="/purchase-orders",
            audience="erp-purchase-api",
            parameters=(parameter,),
            headers=(Attribute(key="x-trace", value="a"), Attribute(key="x-trace", value="b")),
        )


def test_risk_and_evidence_require_unique_codes_and_attributes() -> None:
    signal = RiskSignal(code="signature-valid", severity=RiskSeverity.LOW, detail="valid")
    assessment = RiskAssessment(
        score=percentage("12.5"),
        verification_level=VerificationLevel.V1_TARGETED,
        policy=policy(),
        signals=(signal,),
    )

    assert assessment.score == Decimal("12.5")
    with pytest.raises(ValidationError, match="signal codes"):
        RiskAssessment(
            score=Decimal("20"),
            verification_level=VerificationLevel.V1_TARGETED,
            policy=policy(),
            signals=(signal, signal),
        )
    with pytest.raises(ValidationError, match="attribute keys"):
        EvidenceEvent(
            event_id="event-001",
            correlation_id="trace-001",
            event_type="document-ingested",
            occurred_at=NOW,
            subject_digest=digest(),
            attributes=(Attribute(key="stage-id", value="a"), Attribute(key="stage-id", value="b")),
        )
