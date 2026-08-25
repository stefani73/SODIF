"""Deterministic product transactions for the gateway workspace."""

from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sodif.domain.canonical import canonical_bytes, sha256_digest
from sodif.domain.enums import HttpMethod, ParameterLocation, SignatureAlgorithm
from sodif.domain.gateway import GatewayDecision, GatewayRequest, GatewayRoutePolicy
from sodif.domain.models import ActionParameter, ExecutionPlan
from sodif.domain.permits import ExecutionPermit, ExecutionPermitClaims, TrustedPermitKey
from sodif.execution import InMemoryApiExecutor
from sodif.gateway.service import SemanticExecutionGateway
from sodif.permits import (
    ExecutionPermitAuthorizer,
    InMemoryPermitConsumptionStore,
    InMemoryPermitTrustStore,
    encode_permit_public_key,
)
from sodif.settings import GatewaySettings

SAMPLE_TIME = datetime(2026, 8, 25, 11, 0, tzinfo=UTC)


class GatewaySampleScenario(StrEnum):
    CONFORMING = "conforming"
    CHANGED_ACTION = "changed_action"
    REPLAYED = "replayed"


class _FixedClock:
    def now(self) -> datetime:
        return SAMPLE_TIME


def run_gateway_sample(
    scenario: GatewaySampleScenario,
    settings: GatewaySettings,
) -> GatewayDecision:
    """Evaluate one representative transaction through the real gateway core."""
    service = _build_gateway(settings)
    approved_plan = _approved_plan(settings)
    execution_permit = _signed_permit(approved_plan)
    transaction_plan = approved_plan
    if scenario is GatewaySampleScenario.CHANGED_ACTION:
        transaction_plan = approved_plan.model_copy(
            update={
                "parameters": tuple(
                    parameter.model_copy(update={"value": Decimal("9250.00")})
                    if parameter.name == "total_amount"
                    else parameter
                    for parameter in approved_plan.parameters
                )
            }
        )
    request = GatewayRequest(
        request_id=f"request-{scenario.value}",
        route_id=settings.route_id,
        plan=transaction_plan,
        permit=execution_permit,
    )
    if scenario is GatewaySampleScenario.REPLAYED:
        service.handle(request)
    return service.handle(request)


def _build_gateway(settings: GatewaySettings) -> SemanticExecutionGateway:
    key = _private_key()
    trusted = TrustedPermitKey(
        key_id="permit-key-product",
        issuer_id="sodif-security",
        algorithm=SignatureAlgorithm.ED25519,
        public_key=encode_permit_public_key(key.public_key()),
        active_from=SAMPLE_TIME - timedelta(days=1),
    )
    authorizer = ExecutionPermitAuthorizer(
        InMemoryPermitTrustStore((trusted,)),
        InMemoryPermitConsumptionStore(),
        _FixedClock(),
    )
    route = GatewayRoutePolicy(
        route_id=settings.route_id,
        audience=settings.audience,
        allowed_methods=(HttpMethod.POST,),
        allowed_path_prefixes=(settings.path_prefix,),
        maximum_parameters=settings.maximum_parameters,
    )
    return SemanticExecutionGateway(
        (route,),
        authorizer,
        InMemoryApiExecutor(_FixedClock()),
        _FixedClock(),
    )


def _approved_plan(settings: GatewaySettings) -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="plan-purchase-order-001",
        intent_digest=_digest("d"),
        method=HttpMethod.POST,
        path=settings.path_prefix,
        audience=settings.audience,
        parameters=(
            ActionParameter(
                name="currency",
                location=ParameterLocation.BODY,
                value="RON",
            ),
            ActionParameter(
                name="supplier_id",
                location=ParameterLocation.BODY,
                value="SUP-2048",
            ),
            ActionParameter(
                name="total_amount",
                location=ParameterLocation.BODY,
                value=Decimal("1250.00"),
            ),
        ),
    )


def _signed_permit(plan: ExecutionPlan) -> ExecutionPermit:
    claims = ExecutionPermitClaims(
        permit_id="permit-purchase-order-001",
        issuer_id="sodif-security",
        key_id="permit-key-product",
        algorithm=SignatureAlgorithm.ED25519,
        document_id="po-2026-0084",
        revision_digest=_digest("a"),
        verification_digest=_digest("b"),
        consensus_digest=_digest("c"),
        intent_digest=plan.intent_digest,
        action_digest=sha256_digest(plan),
        policy_digest=_digest("e"),
        audience=plan.audience,
        issued_at=SAMPLE_TIME - timedelta(seconds=5),
        expires_at=SAMPLE_TIME + timedelta(seconds=55),
    )
    signature = _private_key().sign(canonical_bytes(claims))
    return ExecutionPermit(
        claims=claims,
        signature=urlsafe_b64encode(signature).decode("ascii").rstrip("="),
    )


def _private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes(range(32)))


def _digest(character: str) -> str:
    return f"sha256:{character * 64}"
