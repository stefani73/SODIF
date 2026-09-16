"""Fail-closed gateway orchestration for exact, one-time API actions."""

from datetime import datetime

from sodif.domain.canonical import sha256_digest
from sodif.domain.contracts import ApiExecutor, Clock, PermitAuthorizer
from sodif.domain.execution import ExecutionReceipt
from sodif.domain.gateway import (
    GatewayCheckOutcome,
    GatewayDecision,
    GatewayDecisionStatus,
    GatewayPolicyCheck,
    GatewayRequest,
    GatewayRoutePolicy,
)
from sodif.domain.permits import ExecutionAuthorization
from sodif.execution.errors import ExecutionRejected
from sodif.permits.errors import PermitRejected


class SemanticExecutionGateway:
    """Apply route policy, authorize the signed intent, and execute fail-closed."""

    def __init__(
        self,
        routes: tuple[GatewayRoutePolicy, ...],
        authorizer: PermitAuthorizer,
        executor: ApiExecutor,
        clock: Clock,
    ) -> None:
        keyed_routes = {route.route_id: route for route in routes}
        if not routes:
            raise ValueError("semantic gateway requires at least one route")
        if len(keyed_routes) != len(routes):
            raise ValueError("semantic gateway route identifiers must be unique")
        self._routes = keyed_routes
        self._authorizer = authorizer
        self._executor = executor
        self._clock = clock

    def handle(self, request: GatewayRequest) -> GatewayDecision:
        """Return a routed or blocked decision with complete policy evidence."""
        evaluated_at = self._clock.now()
        checks: list[GatewayPolicyCheck] = []
        route = self._routes.get(request.route_id)
        if route is None:
            checks.append(_failed("route.resolved", "Configured gateway route was not found."))
            return self._blocked(
                request,
                evaluated_at,
                "route.not_found",
                "The requested gateway route is not configured.",
                checks,
            )
        checks.append(_passed("route.resolved", "Gateway route is configured."))

        if request.plan.audience != route.audience:
            checks.append(
                _failed("route.audience", "Request audience differs from the protected service.")
            )
            return self._blocked(
                request,
                evaluated_at,
                "route.audience_mismatch",
                "The transaction is addressed to another protected service.",
                checks,
            )
        checks.append(_passed("route.audience", "Request targets the protected service."))

        if request.plan.method not in route.allowed_methods:
            checks.append(_failed("route.method", "HTTP method is not allowed on this route."))
            return self._blocked(
                request,
                evaluated_at,
                "route.method_not_allowed",
                "The HTTP method is outside the configured route policy.",
                checks,
            )
        checks.append(_passed("route.method", "HTTP method is allowed."))

        if not route.allows_path(request.plan.path):
            checks.append(_failed("route.path", "Request path is outside the protected boundary."))
            return self._blocked(
                request,
                evaluated_at,
                "route.path_not_allowed",
                "The request path is outside the configured route policy.",
                checks,
            )
        checks.append(_passed("route.path", "Request path is covered by the route policy."))

        if len(request.plan.parameters) > route.maximum_parameters:
            checks.append(_failed("request.size", "Request exceeds the parameter limit."))
            return self._blocked(
                request,
                evaluated_at,
                "request.parameter_limit",
                "The transaction exceeds the configured request complexity limit.",
                checks,
            )
        checks.append(_passed("request.size", "Request stays within the parameter limit."))

        try:
            authorization = self._authorizer.authorize(
                request.permit,
                request.plan,
                route.audience,
                request.execution_proof,
            )
        except PermitRejected as error:
            checks.append(_failed("permit.authorization", error.detail))
            return self._blocked(
                request,
                evaluated_at,
                f"permit.{error.code.value}",
                error.detail,
                checks,
            )
        checks.append(
            _passed(
                "permit.authorization",
                "Signature, semantic field proofs, action binding, audience and one-time use "
                "are valid.",
            )
        )

        try:
            receipt = self._executor.execute(authorization, request.plan)
        except ExecutionRejected as error:
            checks.append(_failed("upstream.execution", str(error)))
            return self._blocked(
                request,
                evaluated_at,
                "upstream.execution_rejected",
                "The protected service adapter rejected the authorized transaction.",
                checks,
            )
        checks.append(_passed("upstream.execution", "Protected service accepted the transaction."))
        return self._decision(
            request,
            evaluated_at,
            GatewayDecisionStatus.ROUTED,
            "route.authorized",
            "The request matches the signed intent and was routed exactly once.",
            checks,
            authorization=authorization,
            receipt=receipt,
        )

    def _blocked(
        self,
        request: GatewayRequest,
        evaluated_at: datetime,
        code: str,
        detail: str,
        checks: list[GatewayPolicyCheck],
    ) -> GatewayDecision:
        return self._decision(
            request,
            evaluated_at,
            GatewayDecisionStatus.BLOCKED,
            code,
            detail,
            checks,
        )

    def _decision(
        self,
        request: GatewayRequest,
        evaluated_at: datetime,
        status: GatewayDecisionStatus,
        code: str,
        detail: str,
        checks: list[GatewayPolicyCheck],
        *,
        authorization: ExecutionAuthorization | None = None,
        receipt: ExecutionReceipt | None = None,
    ) -> GatewayDecision:
        request_digest = sha256_digest(request)
        identity = sha256_digest(
            {
                "request_digest": request_digest,
                "status": status,
                "code": code,
                "evaluated_at": evaluated_at,
            }
        )
        return GatewayDecision.model_validate(
            {
                "decision_id": f"gateway-{identity[7:23]}",
                "request_id": request.request_id,
                "request_digest": request_digest,
                "permit_id": request.permit.claims.permit_id,
                "route_id": request.route_id,
                "audience": request.plan.audience,
                "observed_action_digest": sha256_digest(request.plan),
                "authorized_action_digest": request.permit.claims.action_digest,
                "status": status,
                "code": code,
                "detail": detail,
                "evaluated_at": evaluated_at,
                "checks": tuple(checks),
                "authorization": authorization,
                "receipt": receipt,
            }
        )


def _passed(code: str, detail: str) -> GatewayPolicyCheck:
    return GatewayPolicyCheck(code=code, outcome=GatewayCheckOutcome.PASSED, detail=detail)


def _failed(code: str, detail: str) -> GatewayPolicyCheck:
    return GatewayPolicyCheck(code=code, outcome=GatewayCheckOutcome.FAILED, detail=detail)
