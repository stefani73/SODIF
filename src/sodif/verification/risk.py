"""Explainable risk triage selecting the initial verification level."""

from decimal import Decimal

from sodif.domain.enums import (
    HttpMethod,
    RiskSeverity,
    SignatureStatus,
    VerificationLevel,
)
from sodif.domain.models import (
    ActionContext,
    DocumentEnvelope,
    PolicyReference,
    RiskAssessment,
    RiskSignal,
)
from sodif.domain.types import Identifier


class AdaptiveRiskPolicy:
    """Small deterministic policy whose reasons remain auditable."""

    def __init__(
        self,
        policy: PolicyReference,
        manual_review_actions: frozenset[Identifier] | None = None,
    ) -> None:
        self._policy = policy
        self._manual_review_actions = manual_review_actions or frozenset()

    def assess(self, document: DocumentEnvelope, action: ActionContext) -> RiskAssessment:
        invalid_signature = any(
            signature.status is not SignatureStatus.VALID or not signature.covers_revision
            for signature in document.signatures
        )
        if invalid_signature:
            return RiskAssessment(
                score=Decimal("100"),
                verification_level=VerificationLevel.V0_BLOCK,
                policy=self._policy,
                signals=(
                    RiskSignal(
                        code="signed-revision-invalid",
                        severity=RiskSeverity.CRITICAL,
                        detail="At least one signature is invalid or does not cover the revision.",
                    ),
                ),
            )

        score = Decimal("10")
        signals = [
            RiskSignal(
                code="signed-revision-valid",
                severity=RiskSeverity.LOW,
                detail="All declared signatures cover the accepted revision.",
            )
        ]
        method_scores = {
            HttpMethod.PUT: (Decimal("15"), RiskSeverity.LOW),
            HttpMethod.PATCH: (Decimal("30"), RiskSeverity.MEDIUM),
            HttpMethod.DELETE: (Decimal("70"), RiskSeverity.CRITICAL),
        }
        if action.method in method_scores:
            increment, severity = method_scores[action.method]
            score += increment
            signals.append(
                RiskSignal(
                    code=f"method-{action.method.value.lower()}",
                    severity=severity,
                    detail=f"{action.method.value} changes the verification exposure.",
                )
            )
        if document.policy != self._policy:
            score += Decimal("40")
            signals.append(
                RiskSignal(
                    code="policy-context-mismatch",
                    severity=RiskSeverity.HIGH,
                    detail="Document and active verification policies differ.",
                )
            )
        if action.action_type in self._manual_review_actions:
            score += Decimal("60")
            signals.append(
                RiskSignal(
                    code="action-review-required",
                    severity=RiskSeverity.HIGH,
                    detail="The action type is configured for mandatory review.",
                )
            )
        score = min(score, Decimal("100"))
        if score >= Decimal("70"):
            level = VerificationLevel.V3_REVIEW
        elif score >= Decimal("30"):
            level = VerificationLevel.V2_EXTENDED
        else:
            level = VerificationLevel.V1_TARGETED
        return RiskAssessment(
            score=score,
            verification_level=level,
            policy=self._policy,
            signals=tuple(signals),
        )
