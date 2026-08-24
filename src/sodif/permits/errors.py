"""Stable fail-closed outcomes for permit issuance and authorization."""

from enum import StrEnum


class PermitRejectionCode(StrEnum):
    VERIFICATION_NOT_ACCEPTED = "verification_not_accepted"
    CONTEXT_MISMATCH = "context_mismatch"
    INTENT_MISMATCH = "intent_mismatch"
    POLICY_MISMATCH = "policy_mismatch"
    TTL_INVALID = "ttl_invalid"
    UNTRUSTED_ISSUER_KEY = "untrusted_issuer_key"
    ISSUER_KEY_MISMATCH = "issuer_key_mismatch"
    KEY_NOT_ACTIVE = "key_not_active"
    KEY_REVOKED = "key_revoked"
    SIGNATURE_INVALID = "signature_invalid"
    PERMIT_NOT_YET_VALID = "permit_not_yet_valid"
    PERMIT_EXPIRED = "permit_expired"
    AUDIENCE_MISMATCH = "audience_mismatch"
    ACTION_MISMATCH = "action_mismatch"
    PERMIT_REPLAYED = "permit_replayed"


class PermitRejected(ValueError):
    def __init__(self, code: PermitRejectionCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")
