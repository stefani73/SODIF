"""Tests for fail-closed semantic gateway enforcement."""

from base64 import urlsafe_b64encode
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from sodif.domain.canonical import canonical_bytes, sha256_digest
from sodif.domain.contracts import ApiExecutor, ExecutionGateway
from sodif.domain.enums import HttpMethod, ParameterLocation, SignatureAlgorithm
from sodif.domain.execution import ExecutionReceipt
from sodif.domain.gateway import (
    GatewayCheckOutcome,
    GatewayDecision,
    GatewayDecisionStatus,
    GatewayRequest,
    GatewayRoutePolicy,
)
from sodif.domain.models import ActionParameter, ExecutionPlan
from sodif.domain.permits import (
    ExecutionAuthorization,
    ExecutionPermit,
    ExecutionPermitClaims,
    TrustedPermitKey,
)
from sodif.execution import ExecutionRejected, InMemoryApiExecutor
from sodif.gateway import SemanticExecutionGateway
from sodif.permits import (
    ExecutionPermitAuthorizer,
    InMemoryPermitConsumptionStore,
    InMemoryPermitTrustStore,
    encode_permit_public_key,
)

NOW = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class RejectingExecutor:
    def execute(
        self,
        authorization: ExecutionAuthorization,
        plan: ExecutionPlan,
    ) -> ExecutionReceipt:
        raise ExecutionRejected("protected service is unavailable")


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


def plan(
    *,
    audience: str = "erp-api",
    method: HttpMethod = HttpMethod.POST,
    path: str = "/purchase-orders",
    parameters: tuple[ActionParameter, ...] | None = None,
) -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="plan-gateway-001",
        intent_digest=digest("d"),
        method=method,
        path=path,
        audience=audience,
        parameters=parameters
        or (
            ActionParameter(
                name="total_amount",
                location=ParameterLocation.BODY,
                value=Decimal("1250.00"),
            ),
        ),
    )


def private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes(range(32)))


def permit(execution_plan: ExecutionPlan) -> ExecutionPermit:
    claims = ExecutionPermitClaims(
        permit_id="permit-gateway-001",
        issuer_id="sodif-issuer",
        key_id="permit-key-01",
        algorithm=SignatureAlgorithm.ED25519,
        document_id="doc-gateway-001",
        revision_digest=digest("a"),
        verification_digest=digest("b"),
        consensus_digest=digest("c"),
        intent_digest=execution_plan.intent_digest,
        action_digest=sha256_digest(execution_plan),
        policy_digest=digest("e"),
        audience=execution_plan.audience,
        issued_at=NOW - timedelta(seconds=5),
        expires_at=NOW + timedelta(seconds=55),
    )
    signature = urlsafe_b64encode(private_key().sign(canonical_bytes(claims))).decode().rstrip("=")
    return ExecutionPermit(claims=claims, signature=signature)


def route(**updates: object) -> GatewayRoutePolicy:
    values: dict[str, object] = {
        "route_id": "erp.purchase-orders",
        "audience": "erp-api",
        "allowed_methods": (HttpMethod.POST,),
        "allowed_path_prefixes": ("/purchase-orders",),
        "maximum_parameters": 8,
    }
    return GatewayRoutePolicy.model_validate({**values, **updates})


def request(
    execution_plan: ExecutionPlan | None = None,
    execution_permit: ExecutionPermit | None = None,
    *,
    route_id: str = "erp.purchase-orders",
) -> GatewayRequest:
    selected_plan = execution_plan or plan()
    return GatewayRequest(
        request_id="request-gateway-001",
        route_id=route_id,
        plan=selected_plan,
        permit=execution_permit or permit(selected_plan),
    )


def gateway(
    store: InMemoryPermitConsumptionStore | None = None,
    *,
    routes: tuple[GatewayRoutePolicy, ...] | None = None,
    executor: ApiExecutor | None = None,
) -> SemanticExecutionGateway:
    trusted_key = TrustedPermitKey(
        key_id="permit-key-01",
        issuer_id="sodif-issuer",
        algorithm=SignatureAlgorithm.ED25519,
        public_key=encode_permit_public_key(private_key().public_key()),
        active_from=NOW - timedelta(days=1),
    )
    authorizer = ExecutionPermitAuthorizer(
        InMemoryPermitTrustStore((trusted_key,)),
        store or InMemoryPermitConsumptionStore(),
        FixedClock(),
    )
    return SemanticExecutionGateway(
        (route(),) if routes is None else routes,
        authorizer,
        executor or InMemoryApiExecutor(FixedClock()),
        FixedClock(),
    )


def test_valid_transaction_is_authorized_routed_and_auditable() -> None:
    transaction = request()
    service = gateway()

    decision = service.handle(transaction)

    assert isinstance(service, ExecutionGateway)
    assert decision.status is GatewayDecisionStatus.ROUTED
    assert decision.code == "route.authorized"
    assert decision.request_digest == sha256_digest(transaction)
    assert decision.observed_action_digest == decision.authorized_action_digest
    assert decision.authorization is not None
    assert decision.receipt is not None
    assert decision.receipt.response_code == 202
    assert all(check.outcome is GatewayCheckOutcome.PASSED for check in decision.checks)


def test_changed_action_is_blocked_without_consuming_the_permit() -> None:
    approved_plan = plan()
    execution_permit = permit(approved_plan)
    changed = approved_plan.model_copy(
        update={
            "parameters": (
                ActionParameter(
                    name="total_amount",
                    location=ParameterLocation.BODY,
                    value=Decimal("9250.00"),
                ),
            )
        }
    )
    store = InMemoryPermitConsumptionStore()

    decision = gateway(store).handle(request(changed, execution_permit))

    assert decision.status is GatewayDecisionStatus.BLOCKED
    assert decision.code == "permit.action_mismatch"
    assert decision.observed_action_digest != decision.authorized_action_digest
    assert decision.authorization is None
    assert decision.receipt is None
    assert store.get(execution_permit.claims.permit_id) is None


def test_replayed_permit_is_blocked_after_one_successful_route() -> None:
    store = InMemoryPermitConsumptionStore()
    service = gateway(store)
    transaction = request()

    first = service.handle(transaction)
    second = service.handle(transaction)

    assert first.status is GatewayDecisionStatus.ROUTED
    assert second.status is GatewayDecisionStatus.BLOCKED
    assert second.code == "permit.permit_replayed"
    assert second.checks[-1].code == "permit.authorization"
    assert second.checks[-1].outcome is GatewayCheckOutcome.FAILED


@pytest.mark.parametrize(
    ("transaction", "configured_route", "expected_code"),
    [
        (request(route_id="missing-route"), route(), "route.not_found"),
        (request(plan(audience="other-api")), route(), "route.audience_mismatch"),
        (request(plan(method=HttpMethod.PUT)), route(), "route.method_not_allowed"),
        (request(plan(path="/payments")), route(), "route.path_not_allowed"),
        (
            request(
                plan(
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
                    )
                )
            ),
            route(maximum_parameters=1),
            "request.parameter_limit",
        ),
    ],
)
def test_route_policy_blocks_before_permit_consumption(
    transaction: GatewayRequest,
    configured_route: GatewayRoutePolicy,
    expected_code: str,
) -> None:
    store = InMemoryPermitConsumptionStore()

    decision = gateway(store, routes=(configured_route,)).handle(transaction)

    assert decision.status is GatewayDecisionStatus.BLOCKED
    assert decision.code == expected_code
    assert decision.checks[-1].outcome is GatewayCheckOutcome.FAILED
    assert store.get(transaction.permit.claims.permit_id) is None


def test_invalid_signature_and_upstream_rejection_are_fail_closed() -> None:
    transaction = request()
    invalid_permit = transaction.permit.model_copy(update={"signature": "A" * 86})

    invalid = gateway().handle(request(transaction.plan, invalid_permit))
    unavailable = gateway(executor=RejectingExecutor()).handle(transaction)

    assert invalid.status is GatewayDecisionStatus.BLOCKED
    assert invalid.code == "permit.signature_invalid"
    assert unavailable.status is GatewayDecisionStatus.BLOCKED
    assert unavailable.code == "upstream.execution_rejected"


def test_concurrent_replay_barrier_routes_exactly_once() -> None:
    service = gateway(InMemoryPermitConsumptionStore())
    transaction = request()

    with ThreadPoolExecutor(max_workers=8) as executor:
        decisions = list(executor.map(lambda _: service.handle(transaction), range(12)))

    assert sum(item.status is GatewayDecisionStatus.ROUTED for item in decisions) == 1
    assert sum(item.code == "permit.permit_replayed" for item in decisions) == 11


def test_gateway_policy_and_decision_invariants_fail_early() -> None:
    with pytest.raises(ValidationError, match="path prefixes"):
        route(allowed_path_prefixes=("/purchase-orders/",))
    with pytest.raises(ValueError, match="at least one route"):
        gateway(routes=())

    routed = gateway().handle(request())
    with pytest.raises(ValidationError, match="require authorization"):
        GatewayDecision.model_validate(routed.model_dump(exclude={"authorization", "receipt"}))
