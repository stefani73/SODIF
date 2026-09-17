"""Safe in-memory API target used by the TRL 4 flight."""

from threading import RLock

from sodif.domain.canonical import sha256_digest
from sodif.domain.contracts import Clock
from sodif.domain.enums import ApiExecutionStatus, DocumentSecurityMode
from sodif.domain.execution import ExecutionReceipt
from sodif.domain.models import ExecutionPlan
from sodif.domain.permits import ExecutionAuthorization
from sodif.domain.types import Identifier
from sodif.execution.errors import ExecutionRejected


class InMemoryApiExecutor:
    """Record a controlled execution without external side effects."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._receipts: dict[str, ExecutionReceipt] = {}
        self._lock = RLock()

    def execute(
        self,
        authorization: ExecutionAuthorization,
        plan: ExecutionPlan,
    ) -> ExecutionReceipt:
        if authorization.action_digest != sha256_digest(plan):
            raise ExecutionRejected("authorization does not cover the supplied plan")
        if authorization.audience != plan.audience:
            raise ExecutionRejected("authorization audience differs from plan audience")
        execution_id = f"exec-{authorization.permit_id}"
        with self._lock:
            if execution_id in self._receipts:
                raise ExecutionRejected("authorized action was already executed")
            response_digest = sha256_digest(
                {
                    "execution_id": execution_id,
                    "status": "accepted",
                    "action_digest": authorization.action_digest,
                }
            )
            receipt = ExecutionReceipt(
                execution_id=execution_id,
                permit_id=authorization.permit_id,
                action_digest=authorization.action_digest,
                audience=plan.audience,
                method=plan.method,
                path=plan.path,
                status=ApiExecutionStatus.SUCCEEDED,
                response_code=202,
                response_digest=response_digest,
                executed_at=self._clock.now(),
            )
            self._receipts[execution_id] = receipt
            return receipt

    def get(self, execution_id: Identifier) -> ExecutionReceipt | None:
        with self._lock:
            return self._receipts.get(execution_id)


class InMemoryDirectApiAdapter:
    """Record a standard direct transfer without advanced SODIF authorization."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._receipts: dict[str, ExecutionReceipt] = {}
        self._lock = RLock()

    def execute(self, request_id: Identifier, plan: ExecutionPlan) -> ExecutionReceipt:
        action_digest = sha256_digest(plan)
        execution_id = f"direct-{request_id}"
        with self._lock:
            if execution_id in self._receipts:
                raise ExecutionRejected("direct request was already transferred")
            response_digest = sha256_digest(
                {
                    "execution_id": execution_id,
                    "security_mode": DocumentSecurityMode.STANDARD,
                    "status": "accepted",
                    "action_digest": action_digest,
                }
            )
            receipt = ExecutionReceipt(
                execution_id=execution_id,
                permit_id=None,
                action_digest=action_digest,
                audience=plan.audience,
                method=plan.method,
                path=plan.path,
                status=ApiExecutionStatus.SUCCEEDED,
                response_code=202,
                response_digest=response_digest,
                executed_at=self._clock.now(),
                security_mode=DocumentSecurityMode.STANDARD,
            )
            self._receipts[execution_id] = receipt
            return receipt

    def get(self, execution_id: Identifier) -> ExecutionReceipt | None:
        with self._lock:
            return self._receipts.get(execution_id)
