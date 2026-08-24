"""Risk-to-verification-level tests for explainable adaptive routing."""

from datetime import UTC, datetime

import pytest

from sodif.domain.enums import (
    DocumentFormat,
    HttpMethod,
    SignatureStatus,
    VerificationLevel,
)
from sodif.domain.models import (
    ActionContext,
    DocumentEnvelope,
    PolicyReference,
    SignatureEvidence,
)
from sodif.verification.risk import AdaptiveRiskPolicy

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def policy(character: str = "b") -> PolicyReference:
    return PolicyReference(policy_id="policy-01", version="v1", digest=digest(character))


def document(
    status: SignatureStatus = SignatureStatus.VALID,
    covers_revision: bool = True,
    document_policy: PolicyReference | None = None,
) -> DocumentEnvelope:
    return DocumentEnvelope(
        document_id="doc-001",
        format=DocumentFormat.PDF,
        revision_digest=digest("a"),
        signatures=(
            SignatureEvidence(
                signer_id="signer-01",
                status=status,
                covers_revision=covers_revision,
                validated_at=NOW,
                validator_id="validator-01",
                validator_version="v1",
            ),
        ),
        policy=document_policy or policy(),
        ingested_at=NOW,
    )


def action(method: HttpMethod, action_type: str = "create-order") -> ActionContext:
    return ActionContext(
        action_type=action_type,
        method=method,
        path="/orders",
        audience="erp-api",
    )


@pytest.mark.parametrize(
    ("method", "level", "score"),
    [
        (HttpMethod.POST, VerificationLevel.V1_TARGETED, "10"),
        (HttpMethod.PATCH, VerificationLevel.V2_EXTENDED, "40"),
        (HttpMethod.DELETE, VerificationLevel.V3_REVIEW, "80"),
    ],
)
def test_method_exposure_selects_a_proportional_level(
    method: HttpMethod,
    level: VerificationLevel,
    score: str,
) -> None:
    assessment = AdaptiveRiskPolicy(policy()).assess(document(), action(method))

    assert assessment.verification_level is level
    assert str(assessment.score) == score


def test_invalid_or_uncovered_signature_blocks_semantic_processing() -> None:
    risk_policy = AdaptiveRiskPolicy(policy())

    for invalid in (
        document(SignatureStatus.INVALID),
        document(covers_revision=False),
    ):
        assessment = risk_policy.assess(invalid, action(HttpMethod.POST))
        assert assessment.verification_level is VerificationLevel.V0_BLOCK
        assert assessment.signals[0].code == "signed-revision-invalid"


def test_policy_mismatch_and_configured_action_raise_explainable_risk() -> None:
    risk_policy = AdaptiveRiskPolicy(
        policy(),
        manual_review_actions=frozenset({"release-payment"}),
    )

    mismatch = risk_policy.assess(
        document(document_policy=policy("c")),
        action(HttpMethod.POST),
    )
    manual = risk_policy.assess(document(), action(HttpMethod.POST, "release-payment"))

    assert mismatch.verification_level is VerificationLevel.V2_EXTENDED
    assert mismatch.signals[-1].code == "policy-context-mismatch"
    assert manual.verification_level is VerificationLevel.V3_REVIEW
    assert manual.signals[-1].code == "action-review-required"
