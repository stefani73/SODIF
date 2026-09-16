"""Semantic gateway request, policy, and decision contracts."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import HttpMethod
from sodif.domain.execution import ExecutionReceipt
from sodif.domain.invariance import ExecutionProofBundle
from sodif.domain.models import ExecutionPlan
from sodif.domain.permits import ExecutionAuthorization, ExecutionPermit
from sodif.domain.types import Digest, Identifier


class GatewayDecisionStatus(StrEnum):
    ROUTED = "routed"
    BLOCKED = "blocked"


class GatewayCheckOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class GatewayRoutePolicy(DomainModel):
    route_id: Identifier
    audience: Identifier
    allowed_methods: tuple[HttpMethod, ...] = Field(min_length=1)
    allowed_path_prefixes: tuple[str, ...] = Field(min_length=1)
    maximum_parameters: int = Field(default=32, ge=1, le=256)

    @model_validator(mode="after")
    def route_constraints_are_unambiguous(self) -> Self:
        if len(self.allowed_methods) != len(set(self.allowed_methods)):
            raise ValueError("gateway route methods must be unique")
        if len(self.allowed_path_prefixes) != len(set(self.allowed_path_prefixes)):
            raise ValueError("gateway path prefixes must be unique")
        if any(
            not prefix.startswith("/") or prefix.endswith("/")
            for prefix in self.allowed_path_prefixes
        ):
            raise ValueError("gateway path prefixes must start with / and omit a trailing /")
        return self

    def allows_path(self, path: str) -> bool:
        return any(
            path == prefix or path.startswith(f"{prefix}/") for prefix in self.allowed_path_prefixes
        )


class GatewayRequest(DomainModel):
    protocol: Literal["sodif.gateway-request/v2"] = "sodif.gateway-request/v2"
    request_id: Identifier
    route_id: Identifier
    plan: ExecutionPlan
    execution_proof: ExecutionProofBundle
    permit: ExecutionPermit


class GatewayPolicyCheck(DomainModel):
    code: Identifier
    outcome: GatewayCheckOutcome
    detail: str = Field(min_length=1, max_length=500)


class GatewayDecision(DomainModel):
    protocol: Literal["sodif.gateway-decision/v1"] = "sodif.gateway-decision/v1"
    decision_id: Identifier
    request_id: Identifier
    request_digest: Digest
    permit_id: Identifier
    route_id: Identifier
    audience: Identifier
    observed_action_digest: Digest
    authorized_action_digest: Digest
    status: GatewayDecisionStatus
    code: Identifier
    detail: str = Field(min_length=1, max_length=500)
    evaluated_at: AwareDatetime
    checks: tuple[GatewayPolicyCheck, ...] = Field(min_length=1)
    authorization: ExecutionAuthorization | None = None
    receipt: ExecutionReceipt | None = None

    @model_validator(mode="after")
    def outcome_contains_consistent_evidence(self) -> Self:
        codes = [check.code for check in self.checks]
        if len(codes) != len(set(codes)):
            raise ValueError("gateway policy check codes must be unique")
        if self.status is GatewayDecisionStatus.ROUTED:
            if self.authorization is None or self.receipt is None:
                raise ValueError("routed gateway decisions require authorization and receipt")
        elif self.authorization is not None or self.receipt is not None:
            raise ValueError("blocked gateway decisions cannot contain execution evidence")
        return self
