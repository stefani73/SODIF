"""Deterministic end-to-end flight across the core SODIF controls."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sodif.archive import (
    ArchiveRepository,
    DocumentArchiveService,
    InMemoryArchiveRepository,
    SqliteArchiveRepository,
)
from sodif.demo.adapters import ScenarioSemanticAdapter, ScenarioValue
from sodif.demo.fixtures import (
    BASE_PDF,
    REVISED_PDF,
    TAMPERED_PDF,
    accepted_values,
    flight_policy,
    purchase_order_action,
    purchase_order_schema,
)
from sodif.demo.models import (
    FlightKind,
    FlightReport,
    FlightScenario,
    ScenarioObservation,
    ScenarioOutcome,
    ScenarioResult,
)
from sodif.documents import (
    DocumentRejected,
    Ed25519RevisionSigner,
    InMemoryRevisionRepository,
    InMemoryTrustStore,
    SignedRevisionService,
    demo_revision_signer,
    demo_trusted_signer,
)
from sodif.domain.canonical import sha256_bytes, sha256_digest
from sodif.domain.enums import (
    DocumentFormat,
    HttpMethod,
    ProcessingStage,
    SignatureAlgorithm,
    VerificationOutcomeStatus,
    ViewKind,
)
from sodif.domain.execution import ExecutionReceipt
from sodif.domain.gateway import (
    GatewayDecision,
    GatewayDecisionStatus,
    GatewayRequest,
    GatewayRoutePolicy,
)
from sodif.domain.models import DocumentEnvelope, ExecutionPlan, PolicyReference
from sodif.domain.permits import ExecutionPermit, TrustedPermitKey
from sodif.domain.revisions import SignedRevision, SignedRevisionMetadata
from sodif.domain.schemas import IntentSchema
from sodif.domain.state import WorkflowState, transition
from sodif.domain.verification import AdaptiveVerificationOutcome
from sodif.execution import (
    ConsensusIntentAssembler,
    DeterministicActionCompiler,
    InMemoryApiExecutor,
)
from sodif.gateway import SemanticExecutionGateway
from sodif.permits import (
    Ed25519PermitIssuer,
    ExecutionPermitAuthorizer,
    InMemoryPermitConsumptionStore,
    InMemoryPermitTrustStore,
    PermitRejected,
    encode_permit_public_key,
)
from sodif.verification import AdaptiveRiskPolicy, AdaptiveVerificationService
from sodif.verification.consensus import DeterministicConsensusEngine

FLIGHT_START = datetime(2026, 8, 24, 14, 0, tzinfo=UTC)


@dataclass
class ScenarioClock:
    current: datetime

    def now(self) -> datetime:
        result = self.current
        self.current += timedelta(seconds=1)
        return result


@dataclass(frozen=True, slots=True)
class ScenarioPermitIdSource:
    scenario_id: FlightScenario

    def new_id(self) -> str:
        return f"permit-{self.scenario_id.value}"


@dataclass
class _ScenarioContext:
    scenario_id: FlightScenario
    clock: ScenarioClock
    workflow: WorkflowState
    observations: list[ScenarioObservation]
    policy: PolicyReference
    schema: IntentSchema
    document_signer: Ed25519RevisionSigner
    document_service: SignedRevisionService
    archive_service: DocumentArchiveService | None
    permit_issuer: Ed25519PermitIssuer
    permit_authorizer: ExecutionPermitAuthorizer
    api_executor: InMemoryApiExecutor
    gateway: SemanticExecutionGateway | None
    archive_ids: list[str]

    def observe(self, stage: str, detail: str, subject_digest: str | None = None) -> None:
        self.observations.append(
            ScenarioObservation(
                sequence=len(self.observations) + 1,
                stage=stage,
                detail=detail,
                occurred_at=self.clock.now(),
                subject_digest=subject_digest,
            )
        )

    def move(self, stage: ProcessingStage, reason: str) -> None:
        self.workflow = transition(self.workflow, stage, self.clock.now(), reason)


class FlightRunner:
    """Run the fixed minimal scenario catalog and return report-ready evidence."""

    def __init__(
        self,
        archive_repository: ArchiveRepository | None = None,
        *,
        flight_kind: FlightKind = FlightKind.SECURITY,
    ) -> None:
        if flight_kind is FlightKind.SECURITY and archive_repository is not None:
            raise ValueError("security flight cannot use a document archive")
        self._flight_kind = flight_kind
        self._archive_repository = archive_repository

    def run(self) -> FlightReport:
        results = (
            self._happy_path(),
            self._adaptive_recovery(),
            self._tampered_document(),
            self._semantic_conflict(),
            self._action_tampering(),
            self._replay_attack(),
        )
        report_digest = sha256_digest({"flight_kind": self._flight_kind, "results": results})
        return FlightReport(
            report_id=f"flight-{report_digest[7:23]}",
            flight_kind=self._flight_kind,
            release="0.17.0-transversal3",
            started_at=FLIGHT_START,
            completed_at=FLIGHT_START + timedelta(minutes=5),
            results=results,
            passed=all(result.passed for result in results),
            passed_scenarios=sum(result.passed for result in results),
        )

    def _happy_path(self) -> ScenarioResult:
        context, document, verification = self._verify(
            FlightScenario.HAPPY_PATH,
            accepted_values(),
            accepted_values(),
        )
        plan, permit = self._compile_and_issue(context, document, verification)
        receipt, gateway_decisions = self._execute(context, plan, permit)
        self._archive_follow_up_revision(context)
        return self._result(
            context,
            "Flux valid cu oprire adaptivă timpurie",
            ScenarioOutcome.EXECUTED,
            verification=verification,
            permit=permit,
            gateway_decisions=gateway_decisions,
            receipt=receipt,
        )

    def _adaptive_recovery(self) -> ScenarioResult:
        visual_values = accepted_values()
        visual_values.pop("total_amount")
        context, document, verification = self._verify(
            FlightScenario.ADAPTIVE_RECOVERY,
            visual_values,
            accepted_values(),
        )
        plan, permit = self._compile_and_issue(context, document, verification)
        receipt, gateway_decisions = self._execute(context, plan, permit)
        return self._result(
            context,
            "Dovadă lipsă rezolvată prin extensie adaptivă",
            ScenarioOutcome.EXECUTED,
            verification=verification,
            permit=permit,
            gateway_decisions=gateway_decisions,
            receipt=receipt,
        )

    def _tampered_document(self) -> ScenarioResult:
        context = self._context(FlightScenario.TAMPERED_DOCUMENT)
        signed_revision = self._signed_revision(context, BASE_PDF)
        try:
            context.document_service.validate(TAMPERED_PDF, signed_revision, context.policy)
        except DocumentRejected as exc:
            context.move(ProcessingStage.BLOCKED, exc.code.value)
            context.observe(
                "document-blocked",
                "Octeții primiți nu mai corespund digestului acoperit de semnătură.",
                sha256_bytes(TAMPERED_PDF),
            )
            return self._result(
                context,
                "Document modificat după semnare",
                ScenarioOutcome.BLOCKED,
                rejection_code=exc.code.value,
            )
        raise AssertionError("tampered document was unexpectedly accepted")

    def _semantic_conflict(self) -> ScenarioResult:
        conflicting = accepted_values(Decimal("9250.00"))
        context, _document, verification = self._verify(
            FlightScenario.SEMANTIC_CONFLICT,
            conflicting,
            accepted_values(),
        )
        if verification.status is not VerificationOutcomeStatus.ESCALATED:
            raise AssertionError("critical semantic conflict was unexpectedly accepted")
        return self._result(
            context,
            "Conflict semantic pe valoarea critică",
            ScenarioOutcome.ESCALATED,
            verification=verification,
            rejection_code=verification.reasons[0],
        )

    def _action_tampering(self) -> ScenarioResult:
        context, document, verification = self._verify(
            FlightScenario.ACTION_TAMPERING,
            accepted_values(),
            accepted_values(),
        )
        plan, permit = self._compile_and_issue(context, document, verification)
        changed_plan = plan.model_copy(update={"path": "/purchase-orders/privileged"})
        if context.gateway is not None:
            decision = context.gateway.handle(
                self._gateway_request(context, changed_plan, permit, "changed-action")
            )
            if decision.status is not GatewayDecisionStatus.BLOCKED:
                raise AssertionError("changed action was unexpectedly routed")
            context.move(ProcessingStage.BLOCKED, decision.code)
            context.observe(
                "gateway-blocked",
                "Gateway-ul a respins ruta care nu mai corespunde acțiunii semnate.",
                sha256_digest(decision),
            )
            return self._result(
                context,
                "Modificarea acțiunii după emiterea permisului",
                ScenarioOutcome.BLOCKED,
                verification=verification,
                permit=permit,
                gateway_decisions=(decision,),
                rejection_code=decision.code,
            )
        try:
            context.permit_authorizer.authorize(permit, changed_plan, plan.audience)
        except PermitRejected as exc:
            context.move(ProcessingStage.BLOCKED, exc.code.value)
            context.observe(
                "action-blocked",
                "Ruta API modificată nu corespunde digestului de acțiune din permis.",
                sha256_digest(changed_plan),
            )
            return self._result(
                context,
                "Modificarea acțiunii după emiterea permisului",
                ScenarioOutcome.BLOCKED,
                verification=verification,
                permit=permit,
                rejection_code=exc.code.value,
            )
        raise AssertionError("changed action was unexpectedly authorized")

    def _replay_attack(self) -> ScenarioResult:
        context, document, verification = self._verify(
            FlightScenario.REPLAY_ATTACK,
            accepted_values(),
            accepted_values(),
        )
        plan, permit = self._compile_and_issue(context, document, verification)
        if context.gateway is not None:
            request = self._gateway_request(context, plan, permit, "replay")
            first_decision = context.gateway.handle(request)
            if first_decision.status is not GatewayDecisionStatus.ROUTED:
                raise AssertionError("first permit presentation was unexpectedly blocked")
            context.observe(
                "gateway-routed",
                "Prima cerere conformă a fost autorizată, rutată și executată o singură dată.",
                sha256_digest(first_decision),
            )
            second_decision = context.gateway.handle(request)
            if second_decision.status is not GatewayDecisionStatus.BLOCKED:
                raise AssertionError("permit replay was unexpectedly routed")
            context.move(ProcessingStage.BLOCKED, second_decision.code)
            context.observe(
                "gateway-blocked",
                "Gateway-ul a respins repetarea aceleiași tranzacții autorizate.",
                sha256_digest(second_decision),
            )
            return self._result(
                context,
                "Reutilizarea permisului consumat",
                ScenarioOutcome.BLOCKED,
                verification=verification,
                permit=permit,
                gateway_decisions=(first_decision, second_decision),
                rejection_code=second_decision.code,
            )
        context.permit_authorizer.authorize(permit, plan, plan.audience)
        context.observe(
            "permit-consumed",
            "Prima prezentare validă a consumat atomic permisul.",
            permit.claims.action_digest,
        )
        try:
            context.permit_authorizer.authorize(permit, plan, plan.audience)
        except PermitRejected as exc:
            context.move(ProcessingStage.BLOCKED, exc.code.value)
            context.observe(
                "replay-blocked",
                "A doua prezentare a aceluiași permis a fost respinsă.",
                permit.claims.action_digest,
            )
            return self._result(
                context,
                "Reutilizarea permisului consumat",
                ScenarioOutcome.BLOCKED,
                verification=verification,
                permit=permit,
                rejection_code=exc.code.value,
            )
        raise AssertionError("permit replay was unexpectedly authorized")

    def _verify(
        self,
        scenario_id: FlightScenario,
        visual_values: dict[str, ScenarioValue],
        target_values: dict[str, ScenarioValue],
    ) -> tuple[_ScenarioContext, DocumentEnvelope, AdaptiveVerificationOutcome]:
        context = self._context(scenario_id)
        signed_revision = self._signed_revision(context, BASE_PDF)
        acceptance = context.document_service.validate(BASE_PDF, signed_revision, context.policy)
        context.move(ProcessingStage.REVISION_VALIDATED, "signed revision validated")
        context.observe(
            "revision-validated",
            "Semnătura și digestul reviziei sunt valide.",
            acceptance.record.revision_digest,
        )
        if context.archive_service is not None:
            archived = context.archive_service.archive(
                BASE_PDF,
                acceptance,
                "comanda-achizitie-demo.pdf",
            )
            context.archive_ids.append(archived.archive_id)
            context.observe(
                "document-archived",
                "Revizia validată a fost înregistrată în arhiva documentară verificabilă.",
                sha256_digest(archived),
            )
        adapters = (
            ScenarioSemanticAdapter(ViewKind.STRUCTURAL, 1, accepted_values()),
            ScenarioSemanticAdapter(ViewKind.VISUAL, 3, visual_values),
            ScenarioSemanticAdapter(ViewKind.TARGET, 2, target_values),
        )
        verifier = AdaptiveVerificationService(
            AdaptiveRiskPolicy(context.policy),
            DeterministicConsensusEngine(),
            adapters,
        )
        verification = verifier.verify(
            acceptance.envelope,
            BASE_PDF,
            context.schema,
            purchase_order_action(),
        )
        context.move(ProcessingStage.RISK_TRIAGED, verification.initial_level.value)
        context.observe(
            "risk-triaged",
            f"Nivel inițial {verification.initial_level.value}; scor {verification.risk.score}.",
            sha256_digest(verification.risk),
        )
        context.move(ProcessingStage.VIEWS_READY, "semantic views ready")
        context.observe(
            "semantic-views",
            (
                f"Au fost executate {len(verification.views)} căi, "
                f"cost {verification.total_cost_units}."
            ),
            sha256_digest(verification.views),
        )
        if verification.status is VerificationOutcomeStatus.ACCEPTED:
            context.move(ProcessingStage.CONSENSUS_ACCEPTED, "semantic consensus accepted")
            context.observe(
                "consensus-accepted",
                "Câmpurile critice au consens independent și proveniență completă.",
                sha256_digest(verification.final_consensus),
            )
        else:
            context.move(ProcessingStage.ESCALATED, verification.reasons[0])
            context.observe(
                "consensus-escalated",
                "Conflictul critic rămâne deschis; permisul nu poate fi emis.",
                sha256_digest(verification.final_consensus),
            )
        return context, acceptance.envelope, verification

    def _compile_and_issue(
        self,
        context: _ScenarioContext,
        document: DocumentEnvelope,
        verification: AdaptiveVerificationOutcome,
    ) -> tuple[ExecutionPlan, ExecutionPermit]:
        if verification.final_consensus is None:
            raise AssertionError("accepted verification lacks consensus")
        manifest = ConsensusIntentAssembler().assemble(
            document,
            verification.final_consensus,
            context.schema,
            context.policy,
        )
        plan = DeterministicActionCompiler().compile(manifest, purchase_order_action())
        context.move(ProcessingStage.ACTION_COMPILED, "intent compiled into exact API action")
        context.observe(
            "action-compiled",
            "Manifestul acceptat a fost compilat într-un plan API determinist.",
            sha256_digest(plan),
        )
        permit = context.permit_issuer.issue(verification, manifest, plan)
        context.move(ProcessingStage.PERMIT_ISSUED, "one-time execution permit issued")
        context.observe(
            "permit-issued",
            "Permisul Ed25519 leagă verificarea de plan și audiență.",
            sha256_digest(permit),
        )
        return plan, permit

    @staticmethod
    def _signed_revision(
        context: _ScenarioContext,
        content: bytes,
        *,
        revision_number: int = 1,
        previous_revision_digest: str | None = None,
        signed_at: datetime | None = None,
    ) -> SignedRevision:
        metadata = SignedRevisionMetadata(
            document_id="doc-flight-001",
            revision_number=revision_number,
            format=DocumentFormat.PDF,
            content_digest=sha256_bytes(content),
            previous_revision_digest=previous_revision_digest,
            signer_id=context.document_signer.signer_id,
            key_id=context.document_signer.key_id,
            algorithm=SignatureAlgorithm.ED25519,
            signed_at=signed_at or FLIGHT_START - timedelta(minutes=1),
        )
        return context.document_signer.sign(metadata)

    @staticmethod
    def _result(
        context: _ScenarioContext,
        title: str,
        outcome: ScenarioOutcome,
        *,
        verification: AdaptiveVerificationOutcome | None = None,
        permit: ExecutionPermit | None = None,
        gateway_decisions: tuple[GatewayDecision, ...] = (),
        receipt: ExecutionReceipt | None = None,
        rejection_code: str | None = None,
    ) -> ScenarioResult:
        return ScenarioResult(
            scenario_id=context.scenario_id,
            title=title,
            expected_outcome=outcome,
            observed_outcome=outcome,
            passed=True,
            workflow=context.workflow,
            observations=tuple(context.observations),
            verification=verification,
            archive_id=context.archive_ids[-1] if context.archive_ids else None,
            archive_ids=tuple(context.archive_ids),
            permit_id=permit.claims.permit_id if permit is not None else None,
            gateway_decisions=gateway_decisions,
            receipt=receipt,
            rejection_code=rejection_code,
        )

    def _context(self, scenario_id: FlightScenario) -> _ScenarioContext:
        clock = ScenarioClock(FLIGHT_START)
        policy = flight_policy()
        document_signer = demo_revision_signer()
        document_trust = demo_trusted_signer()
        document_service = SignedRevisionService(
            InMemoryTrustStore((document_trust,)),
            InMemoryRevisionRepository(),
            clock,
        )
        permit_private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(65, 97)))
        permit_issuer = Ed25519PermitIssuer(
            "flight-permit-issuer",
            "flight-permit-key",
            permit_private_key,
            clock,
            ScenarioPermitIdSource(scenario_id),
        )
        permit_trust = TrustedPermitKey(
            key_id=permit_issuer.key_id,
            issuer_id=permit_issuer.issuer_id,
            algorithm=SignatureAlgorithm.ED25519,
            public_key=encode_permit_public_key(permit_issuer.public_key()),
            active_from=FLIGHT_START - timedelta(days=1),
        )
        permit_authorizer = ExecutionPermitAuthorizer(
            InMemoryPermitTrustStore((permit_trust,)),
            InMemoryPermitConsumptionStore(),
            clock,
        )
        api_executor = InMemoryApiExecutor(clock)
        gateway = (
            SemanticExecutionGateway(
                (
                    GatewayRoutePolicy(
                        route_id="erp.purchase-orders",
                        audience="erp-purchase-api",
                        allowed_methods=(HttpMethod.POST,),
                        allowed_path_prefixes=("/purchase-orders",),
                        maximum_parameters=16,
                    ),
                ),
                permit_authorizer,
                api_executor,
                clock,
            )
            if self._flight_kind is FlightKind.TRANSVERSAL
            else None
        )
        return _ScenarioContext(
            scenario_id=scenario_id,
            clock=clock,
            workflow=WorkflowState(correlation_id=f"flight-{scenario_id.value}"),
            observations=[],
            policy=policy,
            schema=purchase_order_schema(),
            document_signer=document_signer,
            document_service=document_service,
            archive_service=(
                DocumentArchiveService(self._archive_repository, clock)
                if self._archive_repository is not None
                else None
            ),
            archive_ids=[],
            permit_issuer=permit_issuer,
            permit_authorizer=permit_authorizer,
            api_executor=api_executor,
            gateway=gateway,
        )

    @staticmethod
    def _gateway_request(
        context: _ScenarioContext,
        plan: ExecutionPlan,
        permit: ExecutionPermit,
        purpose: str,
    ) -> GatewayRequest:
        return GatewayRequest(
            request_id=f"request-{context.scenario_id.value}-{purpose}",
            route_id="erp.purchase-orders",
            plan=plan,
            permit=permit,
        )

    def _execute(
        self,
        context: _ScenarioContext,
        plan: ExecutionPlan,
        permit: ExecutionPermit,
    ) -> tuple[ExecutionReceipt, tuple[GatewayDecision, ...]]:
        if context.gateway is None:
            authorization = context.permit_authorizer.authorize(permit, plan, plan.audience)
            receipt = context.api_executor.execute(authorization, plan)
            context.move(ProcessingStage.EXECUTED, "authorized action executed")
            context.observe(
                "api-executed",
                "Permisul a autorizat exact planul compilat; API-ul controlat a răspuns 202.",
                receipt.response_digest,
            )
            return receipt, ()
        decision = context.gateway.handle(
            self._gateway_request(context, plan, permit, "authorized-transaction")
        )
        if decision.status is not GatewayDecisionStatus.ROUTED or decision.receipt is None:
            raise AssertionError("conform transaction was unexpectedly blocked by the gateway")
        context.move(ProcessingStage.EXECUTED, "gateway authorized and routed exact action")
        context.observe(
            "gateway-routed",
            "Gateway-ul a validat permisul și politica rutei, apoi a transmis exact "
            "acțiunea aprobată.",
            sha256_digest(decision),
        )
        return decision.receipt, (decision,)

    def _archive_follow_up_revision(self, context: _ScenarioContext) -> None:
        if context.archive_service is None:
            return
        signed_revision = self._signed_revision(
            context,
            REVISED_PDF,
            revision_number=2,
            previous_revision_digest=sha256_bytes(BASE_PDF),
            signed_at=FLIGHT_START + timedelta(seconds=1),
        )
        acceptance = context.document_service.validate(
            REVISED_PDF,
            signed_revision,
            context.policy,
        )
        archived = context.archive_service.archive(
            REVISED_PDF,
            acceptance,
            "comanda-achizitie-demo-r2.pdf",
        )
        context.archive_ids.append(archived.archive_id)
        context.observe(
            "document-revision-archived",
            "Revizia următoare a continuat verificabil istoricul documentului.",
            sha256_digest(archived),
        )


def run_default_flight() -> FlightReport:
    """Run the funding-core security flight without DMS side effects."""
    return run_security_flight()


def run_security_flight() -> FlightReport:
    """Run signed-intent security controls without document archiving."""
    return FlightRunner(flight_kind=FlightKind.SECURITY).run()


def run_transversal_memory_flight() -> FlightReport:
    """Run all three product modules against an ephemeral archive repository."""
    return FlightRunner(
        InMemoryArchiveRepository(),
        flight_kind=FlightKind.TRANSVERSAL,
    ).run()


def run_transversal_flight(archive_root: Path) -> FlightReport:
    """Run all three product modules against the persistent local archive."""
    return FlightRunner(
        SqliteArchiveRepository(archive_root),
        flight_kind=FlightKind.TRANSVERSAL,
    ).run()


def run_archived_flight(archive_root: Path) -> FlightReport:
    """Compatibility alias for the persistent transversal product flight."""
    return run_transversal_flight(archive_root)
