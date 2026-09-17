"""Controlled API execution evidence."""

from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from sodif.domain.base import DomainModel
from sodif.domain.enums import ApiExecutionStatus, DocumentSecurityMode, HttpMethod
from sodif.domain.types import Digest, Identifier


class ExecutionReceipt(DomainModel):
    execution_id: Identifier
    permit_id: Identifier | None
    action_digest: Digest
    audience: Identifier
    method: HttpMethod
    path: str = Field(pattern=r"^/[A-Za-z0-9._~!$&'()*+,;=:@%/-]+$")
    status: ApiExecutionStatus
    response_code: int = Field(ge=200, le=599)
    response_digest: Digest
    executed_at: AwareDatetime
    security_mode: DocumentSecurityMode = DocumentSecurityMode.ADVANCED

    @model_validator(mode="after")
    def authorization_matches_security_mode(self) -> Self:
        if self.security_mode is DocumentSecurityMode.ADVANCED and self.permit_id is None:
            raise ValueError("advanced execution receipts require an execution permit")
        if self.security_mode is DocumentSecurityMode.STANDARD and self.permit_id is not None:
            raise ValueError("standard execution receipts cannot reference an execution permit")
        return self
