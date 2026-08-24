"""Compile a typed intent into an exact API execution plan."""

from sodif.domain.canonical import sha256_digest
from sodif.domain.enums import ParameterLocation
from sodif.domain.models import (
    ActionContext,
    ActionParameter,
    ExecutionPlan,
    IntentManifest,
)
from sodif.execution.errors import ExecutionRejected


class DeterministicActionCompiler:
    def compile(self, manifest: IntentManifest, target: ActionContext) -> ExecutionPlan:
        if manifest.action_type != target.action_type:
            raise ExecutionRejected("intent action_type differs from target action")
        intent_digest = sha256_digest(manifest)
        parameters = tuple(
            ActionParameter(
                name=field.name,
                location=ParameterLocation.BODY,
                value=field.value,
            )
            for field in sorted(manifest.fields, key=lambda item: item.name)
        )
        plan_identity = sha256_digest(
            {
                "intent_digest": intent_digest,
                "method": target.method,
                "path": target.path,
                "audience": target.audience,
                "parameters": parameters,
            }
        )
        return ExecutionPlan(
            plan_id=f"plan-{plan_identity[7:23]}",
            intent_digest=intent_digest,
            method=target.method,
            path=target.path,
            audience=target.audience,
            parameters=parameters,
        )
