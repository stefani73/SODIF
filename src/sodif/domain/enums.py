"""Closed vocabularies used across the domain core."""

from enum import StrEnum


class DocumentFormat(StrEnum):
    PDF = "pdf"


class SignatureStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    INDETERMINATE = "indeterminate"


class SignatureAlgorithm(StrEnum):
    ED25519 = "Ed25519"


class VerificationLevel(StrEnum):
    V0_BLOCK = "v0_block"
    V1_TARGETED = "v1_targeted"
    V2_EXTENDED = "v2_extended"
    V3_REVIEW = "v3_review"


class VerificationOutcomeStatus(StrEnum):
    ACCEPTED = "accepted"
    ESCALATED = "escalated"
    BLOCKED = "blocked"


class ViewKind(StrEnum):
    STRUCTURAL = "structural"
    VISUAL = "visual"
    TARGET = "target"


class SemanticDataType(StrEnum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    CURRENCY = "currency"
    IDENTIFIER = "identifier"
    BOOLEAN = "boolean"


class ConsensusStatus(StrEnum):
    ACCEPTED = "accepted"
    CONFLICT = "conflict"
    MISSING = "missing"


class HttpMethod(StrEnum):
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ParameterLocation(StrEnum):
    BODY = "body"
    PATH = "path"
    HEADER = "header"
    QUERY = "query"


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStage(StrEnum):
    RECEIVED = "received"
    REVISION_VALIDATED = "revision_validated"
    RISK_TRIAGED = "risk_triaged"
    VIEWS_READY = "views_ready"
    CONSENSUS_ACCEPTED = "consensus_accepted"
    ACTION_COMPILED = "action_compiled"
    PERMIT_ISSUED = "permit_issued"
    EXECUTED = "executed"
    ESCALATED = "escalated"
    BLOCKED = "blocked"


class ApiExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
