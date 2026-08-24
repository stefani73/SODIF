"""Controlled API execution evidence."""

from pydantic import AwareDatetime, Field

from sodif.domain.base import DomainModel
from sodif.domain.enums import ApiExecutionStatus, HttpMethod
from sodif.domain.types import Digest, Identifier


class ExecutionReceipt(DomainModel):
    execution_id: Identifier
    permit_id: Identifier
    action_digest: Digest
    audience: Identifier
    method: HttpMethod
    path: str = Field(pattern=r"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]+$")
    status: ApiExecutionStatus
    response_code: int = Field(ge=200, le=599)
    response_digest: Digest
    executed_at: AwareDatetime
