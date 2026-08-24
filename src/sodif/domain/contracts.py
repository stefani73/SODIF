"""Runtime-checkable ports implemented by adapters in later steps."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from sodif.domain.enums import ViewKind
from sodif.domain.models import (
    ActionContext,
    ConsensusResult,
    DocumentEnvelope,
    EvidenceEvent,
    ExecutionPlan,
    IntentManifest,
    PolicyReference,
    RiskAssessment,
    SemanticView,
)
from sodif.domain.revisions import RevisionAcceptance, SignedRevision
from sodif.domain.schemas import IntentSchema
from sodif.domain.types import Identifier


@runtime_checkable
class SignedRevisionValidator(Protocol):
    def validate(
        self,
        content: bytes,
        revision: SignedRevision,
        policy: PolicyReference,
    ) -> RevisionAcceptance: ...


@runtime_checkable
class SemanticAdapter(Protocol):
    @property
    def adapter_id(self) -> Identifier: ...

    @property
    def view_kind(self) -> ViewKind: ...

    @property
    def cost_units(self) -> int: ...

    def extract(
        self,
        document: DocumentEnvelope,
        content: bytes,
        schema: IntentSchema,
    ) -> SemanticView: ...


@runtime_checkable
class RiskPolicy(Protocol):
    def assess(
        self,
        document: DocumentEnvelope,
        action: ActionContext,
    ) -> RiskAssessment: ...


@runtime_checkable
class ConsensusEngine(Protocol):
    def evaluate(
        self,
        views: tuple[SemanticView, ...],
        schema: IntentSchema,
    ) -> ConsensusResult: ...


@runtime_checkable
class IntentAssembler(Protocol):
    def assemble(
        self,
        document: DocumentEnvelope,
        consensus: ConsensusResult,
        schema: IntentSchema,
        policy: PolicyReference,
    ) -> IntentManifest: ...


@runtime_checkable
class ActionCompiler(Protocol):
    def compile(self, manifest: IntentManifest, target: ActionContext) -> ExecutionPlan: ...


@runtime_checkable
class EvidenceSink(Protocol):
    def append(self, correlation_id: Identifier, event: EvidenceEvent) -> None: ...


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...
