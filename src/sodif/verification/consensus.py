"""Schema-driven consensus across independent semantic representations."""

from contextlib import suppress
from dataclasses import dataclass
from decimal import Decimal

from sodif.domain.enums import ConsensusStatus
from sodif.domain.models import (
    CandidateValue,
    ConsensusField,
    ConsensusResult,
    SemanticField,
    SemanticView,
)
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema
from sodif.verification.errors import SemanticNormalizationError, VerificationInputError
from sodif.verification.normalization import NormalizedSemanticValue, normalize_semantic_value


@dataclass(frozen=True, slots=True)
class ConsensusPolicy:
    minimum_independent_views: int = 2
    minimum_confidence: Decimal = Decimal("0.80")
    critical_unanimity: bool = True

    def __post_init__(self) -> None:
        if self.minimum_independent_views < 2:
            raise ValueError("consensus requires at least two independent views")
        if not Decimal("0") <= self.minimum_confidence <= Decimal("1"):
            raise ValueError("minimum_confidence must be between zero and one")


@dataclass(frozen=True, slots=True)
class _ComparableCandidate:
    view: SemanticView
    field: SemanticField
    normalized: NormalizedSemanticValue | None

    @property
    def group_key(self) -> str:
        if self.normalized is None:
            return f"invalid:{self.view.view_id}"
        return self.normalized.comparison_key


class DeterministicConsensusEngine:
    """Require corroboration and preserve every candidate as evidence."""

    def __init__(self, policy: ConsensusPolicy | None = None) -> None:
        self._policy = policy or ConsensusPolicy()

    def evaluate(
        self,
        views: tuple[SemanticView, ...],
        schema: IntentSchema,
    ) -> ConsensusResult:
        document_id, revision_digest = self._validate_views(views)
        fields: list[ConsensusField] = []
        for definition in schema.fields:
            result = self._evaluate_field(views, definition)
            if result is not None:
                fields.append(result)

        if not fields:
            raise VerificationInputError("schema produced no fields for consensus")
        status = ConsensusStatus.ACCEPTED
        if any(field.status is ConsensusStatus.CONFLICT for field in fields):
            status = ConsensusStatus.CONFLICT
        elif any(field.status is ConsensusStatus.MISSING for field in fields):
            status = ConsensusStatus.MISSING
        return ConsensusResult(
            document_id=document_id,
            revision_digest=revision_digest,
            status=status,
            fields=tuple(fields),
        )

    def _validate_views(self, views: tuple[SemanticView, ...]) -> tuple[str, str]:
        if not views:
            raise VerificationInputError("consensus requires semantic views")
        document_ids = {view.document_id for view in views}
        revision_digests = {view.revision_digest for view in views}
        view_ids = {view.view_id for view in views}
        adapter_ids = {view.adapter_id for view in views}
        kinds = {view.kind for view in views}
        if len(document_ids) != 1 or len(revision_digests) != 1:
            raise VerificationInputError("views do not describe the same signed revision")
        if len(view_ids) != len(views):
            raise VerificationInputError("view identifiers must be unique")
        if len(adapter_ids) != len(views) or len(kinds) != len(views):
            raise VerificationInputError("views must come from independent adapters and kinds")
        return next(iter(document_ids)), next(iter(revision_digests))

    def _evaluate_field(
        self,
        views: tuple[SemanticView, ...],
        definition: IntentFieldDefinition,
    ) -> ConsensusField | None:
        comparable: list[_ComparableCandidate] = []
        for view in sorted(views, key=lambda item: item.view_id):
            field = next((item for item in view.fields if item.name == definition.name), None)
            if field is None or field.confidence < self._policy.minimum_confidence:
                continue
            normalized: NormalizedSemanticValue | None = None
            if field.data_type is definition.data_type:
                with suppress(SemanticNormalizationError):
                    normalized = normalize_semantic_value(definition.data_type, field.value)
            comparable.append(_ComparableCandidate(view, field, normalized))

        if not comparable:
            if not definition.required:
                return None
            return self._missing(definition)
        if len(comparable) < self._policy.minimum_independent_views:
            return self._missing(definition)

        groups: dict[str, list[_ComparableCandidate]] = {}
        for item in comparable:
            groups.setdefault(item.group_key, []).append(item)
        candidates = tuple(self._candidate(item) for item in comparable)
        ordered_groups = sorted(
            groups.values(),
            key=lambda group: (-len(group), group[0].group_key),
        )
        winner = ordered_groups[0]
        winner_is_unique = len(ordered_groups) == 1 or len(winner) > len(ordered_groups[1])
        has_conflict = len(ordered_groups) > 1
        if (
            len(winner) < self._policy.minimum_independent_views
            or not winner_is_unique
            or (definition.critical and self._policy.critical_unanimity and has_conflict)
            or winner[0].normalized is None
        ):
            return ConsensusField(
                name=definition.name,
                data_type=definition.data_type,
                status=ConsensusStatus.CONFLICT,
                candidates=candidates,
            )

        preferred = sorted(
            winner,
            key=lambda item: (-item.field.confidence, item.view.view_id),
        )[0]
        assert preferred.normalized is not None
        return ConsensusField(
            name=definition.name,
            data_type=definition.data_type,
            status=ConsensusStatus.ACCEPTED,
            accepted_value=preferred.normalized.canonical_value,
            candidates=candidates,
            supporting_views=tuple(sorted(item.view.view_id for item in winner)),
        )

    @staticmethod
    def _candidate(item: _ComparableCandidate) -> CandidateValue:
        return CandidateValue(
            view_id=item.view.view_id,
            value=item.field.value,
            confidence=item.field.confidence,
            provenance_digest=item.field.provenance.source_digest,
        )

    @staticmethod
    def _missing(definition: IntentFieldDefinition) -> ConsensusField:
        return ConsensusField(
            name=definition.name,
            data_type=definition.data_type,
            status=ConsensusStatus.MISSING,
        )
