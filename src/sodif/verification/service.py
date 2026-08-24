"""Adaptive orchestration that spends extra verification cost only when justified."""

from dataclasses import dataclass

from sodif.domain.contracts import ConsensusEngine, RiskPolicy, SemanticAdapter
from sodif.domain.enums import (
    ConsensusStatus,
    VerificationLevel,
    VerificationOutcomeStatus,
    ViewKind,
)
from sodif.domain.models import ActionContext, DocumentEnvelope, SemanticView
from sodif.domain.schemas import IntentSchema
from sodif.domain.verification import AdaptiveVerificationOutcome, VerificationAttempt
from sodif.verification.errors import VerificationInputError


@dataclass(frozen=True, slots=True)
class AdaptiveRoutePolicy:
    baseline_kinds: tuple[ViewKind, ...] = (ViewKind.STRUCTURAL, ViewKind.VISUAL)
    extended_kinds: tuple[ViewKind, ...] = (
        ViewKind.STRUCTURAL,
        ViewKind.VISUAL,
        ViewKind.TARGET,
    )

    def __post_init__(self) -> None:
        if len(self.baseline_kinds) < 2:
            raise ValueError("baseline route requires two independent view kinds")
        if len(set(self.extended_kinds)) != len(self.extended_kinds):
            raise ValueError("extended route view kinds must be unique")
        if not set(self.baseline_kinds) < set(self.extended_kinds):
            raise ValueError("baseline route must be a strict subset of extended route")


class AdaptiveVerificationService:
    def __init__(
        self,
        risk_policy: RiskPolicy,
        consensus_engine: ConsensusEngine,
        adapters: tuple[SemanticAdapter, ...],
        route_policy: AdaptiveRoutePolicy | None = None,
    ) -> None:
        self._risk_policy = risk_policy
        self._consensus_engine = consensus_engine
        self._route = route_policy or AdaptiveRoutePolicy()
        self._adapters = {adapter.view_kind: adapter for adapter in adapters}
        if len(self._adapters) != len(adapters):
            raise ValueError("semantic adapter view kinds must be unique")
        adapter_ids = {adapter.adapter_id for adapter in adapters}
        if len(adapter_ids) != len(adapters):
            raise ValueError("semantic adapter identifiers must be unique")
        if any(adapter.cost_units < 1 for adapter in adapters):
            raise ValueError("semantic adapter cost_units must be positive")
        missing = set(self._route.extended_kinds) - set(self._adapters)
        if missing:
            labels = sorted(item.value for item in missing)
            raise ValueError(f"missing adapters for view kinds: {labels}")

    def verify(
        self,
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
        action: ActionContext,
    ) -> AdaptiveVerificationOutcome:
        risk = self._risk_policy.assess(document, action)
        available_cost = sum(self._adapters[kind].cost_units for kind in self._route.extended_kinds)
        if risk.verification_level is VerificationLevel.V0_BLOCK:
            return AdaptiveVerificationOutcome(
                document_id=document.document_id,
                revision_digest=document.revision_digest,
                status=VerificationOutcomeStatus.BLOCKED,
                initial_level=VerificationLevel.V0_BLOCK,
                final_level=VerificationLevel.V0_BLOCK,
                risk=risk,
                total_cost_units=0,
                available_cost_units=available_cost,
                reasons=("signed-revision-blocked",),
            )

        initial_kinds = (
            self._route.baseline_kinds
            if risk.verification_level is VerificationLevel.V1_TARGETED
            else self._route.extended_kinds
        )
        views = list(self._extract(initial_kinds, document, content, schema))
        consensus = self._consensus_engine.evaluate(tuple(views), schema)
        initial_adapters = tuple(self._adapters[kind] for kind in initial_kinds)
        attempts = [
            VerificationAttempt(
                level=risk.verification_level,
                adapters_added=tuple(adapter.adapter_id for adapter in initial_adapters),
                view_ids_evaluated=tuple(view.view_id for view in views),
                incremental_cost_units=sum(adapter.cost_units for adapter in initial_adapters),
                consensus=consensus,
            )
        ]
        final_level = risk.verification_level
        if (
            risk.verification_level is VerificationLevel.V1_TARGETED
            and consensus.status is not ConsensusStatus.ACCEPTED
        ):
            additional_kinds = tuple(
                kind for kind in self._route.extended_kinds if kind not in initial_kinds
            )
            added_views = self._extract(additional_kinds, document, content, schema)
            views.extend(added_views)
            consensus = self._consensus_engine.evaluate(tuple(views), schema)
            added_adapters = tuple(self._adapters[kind] for kind in additional_kinds)
            attempts.append(
                VerificationAttempt(
                    level=VerificationLevel.V2_EXTENDED,
                    adapters_added=tuple(adapter.adapter_id for adapter in added_adapters),
                    view_ids_evaluated=tuple(view.view_id for view in views),
                    incremental_cost_units=sum(adapter.cost_units for adapter in added_adapters),
                    consensus=consensus,
                )
            )
            final_level = VerificationLevel.V2_EXTENDED

        if risk.verification_level is VerificationLevel.V3_REVIEW:
            status = VerificationOutcomeStatus.ESCALATED
            reasons = ("risk-review-required",)
        elif consensus.status is ConsensusStatus.ACCEPTED:
            status = VerificationOutcomeStatus.ACCEPTED
            reasons = ("semantic-consensus-accepted",)
        elif consensus.status is ConsensusStatus.CONFLICT:
            status = VerificationOutcomeStatus.ESCALATED
            reasons = ("semantic-conflict",)
        else:
            status = VerificationOutcomeStatus.ESCALATED
            reasons = ("semantic-evidence-missing",)
        return AdaptiveVerificationOutcome(
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            status=status,
            initial_level=risk.verification_level,
            final_level=final_level,
            risk=risk,
            views=tuple(views),
            attempts=tuple(attempts),
            final_consensus=consensus,
            total_cost_units=sum(item.incremental_cost_units for item in attempts),
            available_cost_units=available_cost,
            reasons=reasons,
        )

    def _extract(
        self,
        kinds: tuple[ViewKind, ...],
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
    ) -> tuple[SemanticView, ...]:
        views: list[SemanticView] = []
        for kind in kinds:
            adapter = self._adapters[kind]
            view = adapter.extract(document, content, schema)
            if view.kind is not kind or view.adapter_id != adapter.adapter_id:
                raise VerificationInputError("adapter returned a view with inconsistent identity")
            if (
                view.document_id != document.document_id
                or view.revision_digest != document.revision_digest
            ):
                raise VerificationInputError("adapter returned evidence for another revision")
            views.append(view)
        return tuple(views)
