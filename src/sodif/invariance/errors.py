"""Fail-closed outcomes for semantic invariance evidence."""

from enum import StrEnum


class InvarianceRejectionCode(StrEnum):
    CONTEXT_MISMATCH = "context_mismatch"
    CHALLENGE_PROFILE_MISMATCH = "challenge_profile_mismatch"
    FIELD_NOT_STABLE = "field_not_stable"
    EVIDENCE_CLASS_MISSING = "evidence_class_missing"
    FIELD_ROOT_MISMATCH = "field_root_mismatch"
    ACTION_MISMATCH = "action_mismatch"
    PAYLOAD_COVERAGE_MISSING = "payload_coverage_missing"
    PAYLOAD_VALUE_MISMATCH = "payload_value_mismatch"
    BINDING_ROOT_MISMATCH = "binding_root_mismatch"


class InvarianceRejected(ValueError):
    def __init__(self, code: InvarianceRejectionCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")
