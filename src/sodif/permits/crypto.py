"""Ed25519 permit issuance and exact-action authorization."""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as Base64Error
from dataclasses import dataclass
from datetime import timedelta

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from sodif.domain.canonical import canonical_bytes, sha256_digest
from sodif.domain.contracts import Clock
from sodif.domain.enums import ConsensusStatus, SignatureAlgorithm, VerificationOutcomeStatus
from sodif.domain.models import ExecutionPlan, IntentManifest
from sodif.domain.permits import (
    ExecutionAuthorization,
    ExecutionPermit,
    ExecutionPermitClaims,
    PermitConsumption,
    TrustedPermitKey,
)
from sodif.domain.types import Identifier
from sodif.domain.verification import AdaptiveVerificationOutcome
from sodif.permits.errors import PermitRejected, PermitRejectionCode
from sodif.permits.identifiers import PermitIdSource
from sodif.permits.repository import PermitConsumptionStore


def _encode_unpadded(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_unpadded(value: str, expected_size: int) -> bytes:
    try:
        decoded = urlsafe_b64decode(f"{value}{'=' * (-len(value) % 4)}")
    except (Base64Error, ValueError) as exc:
        raise PermitRejected(
            PermitRejectionCode.SIGNATURE_INVALID,
            "permit signature encoding is invalid",
        ) from exc
    if len(decoded) != expected_size:
        raise PermitRejected(
            PermitRejectionCode.SIGNATURE_INVALID,
            "permit signature has an invalid byte length",
        )
    return decoded


def encode_permit_public_key(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return _encode_unpadded(raw)


@dataclass(frozen=True, slots=True)
class PermitIssuancePolicy:
    default_ttl: timedelta = timedelta(seconds=60)
    maximum_ttl: timedelta = timedelta(minutes=2)

    def __post_init__(self) -> None:
        if self.default_ttl <= timedelta(0) or self.maximum_ttl <= timedelta(0):
            raise ValueError("permit TTL values must be positive")
        if self.default_ttl > self.maximum_ttl:
            raise ValueError("default permit TTL cannot exceed maximum TTL")


class Ed25519PermitIssuer:
    def __init__(
        self,
        issuer_id: Identifier,
        key_id: Identifier,
        private_key: Ed25519PrivateKey,
        clock: Clock,
        id_source: PermitIdSource,
        policy: PermitIssuancePolicy | None = None,
    ) -> None:
        self.issuer_id = issuer_id
        self.key_id = key_id
        self._private_key = private_key
        self._clock = clock
        self._id_source = id_source
        self._policy = policy or PermitIssuancePolicy()

    def public_key(self) -> Ed25519PublicKey:
        return self._private_key.public_key()

    def issue(
        self,
        verification: AdaptiveVerificationOutcome,
        manifest: IntentManifest,
        plan: ExecutionPlan,
        ttl: timedelta | None = None,
    ) -> ExecutionPermit:
        if (
            verification.status is not VerificationOutcomeStatus.ACCEPTED
            or verification.final_consensus is None
            or verification.final_consensus.status is not ConsensusStatus.ACCEPTED
        ):
            raise PermitRejected(
                PermitRejectionCode.VERIFICATION_NOT_ACCEPTED,
                "only automated accepted consensus can produce an execution permit",
            )
        if (
            verification.document_id != manifest.document_id
            or verification.revision_digest != manifest.revision_digest
        ):
            raise PermitRejected(
                PermitRejectionCode.CONTEXT_MISMATCH,
                "verification and intent manifest describe different revisions",
            )
        intent_digest = sha256_digest(manifest)
        if plan.intent_digest != intent_digest:
            raise PermitRejected(
                PermitRejectionCode.INTENT_MISMATCH,
                "execution plan is not derived from the supplied intent manifest",
            )
        if manifest.policy != verification.risk.policy:
            raise PermitRejected(
                PermitRejectionCode.POLICY_MISMATCH,
                "intent and verification policies differ",
            )
        effective_ttl = ttl or self._policy.default_ttl
        if effective_ttl <= timedelta(0) or effective_ttl > self._policy.maximum_ttl:
            raise PermitRejected(
                PermitRejectionCode.TTL_INVALID,
                "permit TTL is outside the issuer policy",
            )
        issued_at = self._clock.now()
        claims = ExecutionPermitClaims(
            permit_id=self._id_source.new_id(),
            issuer_id=self.issuer_id,
            key_id=self.key_id,
            algorithm=SignatureAlgorithm.ED25519,
            document_id=manifest.document_id,
            revision_digest=manifest.revision_digest,
            verification_digest=sha256_digest(verification),
            consensus_digest=sha256_digest(verification.final_consensus),
            intent_digest=intent_digest,
            action_digest=sha256_digest(plan),
            policy_digest=manifest.policy.digest,
            audience=plan.audience,
            issued_at=issued_at,
            expires_at=issued_at + effective_ttl,
        )
        signature = self._private_key.sign(canonical_bytes(claims))
        return ExecutionPermit(claims=claims, signature=_encode_unpadded(signature))


class InMemoryPermitTrustStore:
    def __init__(self, keys: tuple[TrustedPermitKey, ...]) -> None:
        keyed = {key.key_id: key for key in keys}
        if len(keyed) != len(keys):
            raise ValueError("trusted permit key identifiers must be unique")
        self._keys = keyed

    def resolve(self, key_id: Identifier) -> TrustedPermitKey:
        try:
            return self._keys[key_id]
        except KeyError as exc:
            raise PermitRejected(
                PermitRejectionCode.UNTRUSTED_ISSUER_KEY,
                f"permit key {key_id!r} is not trusted",
            ) from exc


@dataclass(frozen=True, slots=True)
class PermitVerificationPolicy:
    maximum_ttl: timedelta = timedelta(minutes=2)

    def __post_init__(self) -> None:
        if self.maximum_ttl <= timedelta(0):
            raise ValueError("maximum permit TTL must be positive")


class ExecutionPermitAuthorizer:
    def __init__(
        self,
        trust_store: InMemoryPermitTrustStore,
        consumption_store: PermitConsumptionStore,
        clock: Clock,
        policy: PermitVerificationPolicy | None = None,
    ) -> None:
        self._trust_store = trust_store
        self._consumption_store = consumption_store
        self._clock = clock
        self._policy = policy or PermitVerificationPolicy()

    def authorize(
        self,
        permit: ExecutionPermit,
        plan: ExecutionPlan,
        expected_audience: Identifier,
    ) -> ExecutionAuthorization:
        claims = permit.claims
        key = self._trust_store.resolve(claims.key_id)
        if key.issuer_id != claims.issuer_id or key.algorithm is not claims.algorithm:
            raise PermitRejected(
                PermitRejectionCode.ISSUER_KEY_MISMATCH,
                "trusted key is not bound to the declared permit issuer",
            )
        if claims.issued_at < key.active_from or (
            key.active_until is not None and claims.issued_at >= key.active_until
        ):
            raise PermitRejected(
                PermitRejectionCode.KEY_NOT_ACTIVE,
                "permit key was not active at issuance time",
            )
        if key.revoked_at is not None and claims.issued_at >= key.revoked_at:
            raise PermitRejected(
                PermitRejectionCode.KEY_REVOKED,
                "permit key was revoked at issuance time",
            )
        raw_signature = _decode_unpadded(permit.signature, expected_size=64)
        raw_public_key = _decode_unpadded(key.public_key, expected_size=32)
        try:
            Ed25519PublicKey.from_public_bytes(raw_public_key).verify(
                raw_signature,
                canonical_bytes(claims),
            )
        except (InvalidSignature, ValueError) as exc:
            raise PermitRejected(
                PermitRejectionCode.SIGNATURE_INVALID,
                "permit signature does not cover the supplied claims",
            ) from exc

        authorized_at = self._clock.now()
        if authorized_at < claims.issued_at:
            raise PermitRejected(
                PermitRejectionCode.PERMIT_NOT_YET_VALID,
                "permit issuance time is in the future",
            )
        if authorized_at >= claims.expires_at:
            raise PermitRejected(
                PermitRejectionCode.PERMIT_EXPIRED,
                "permit validity window has ended",
            )
        if claims.expires_at - claims.issued_at > self._policy.maximum_ttl:
            raise PermitRejected(
                PermitRejectionCode.TTL_INVALID,
                "permit validity window exceeds verifier policy",
            )
        if claims.audience != expected_audience or plan.audience != expected_audience:
            raise PermitRejected(
                PermitRejectionCode.AUDIENCE_MISMATCH,
                "permit and execution plan are not addressed to the expected audience",
            )
        if (
            claims.action_digest != sha256_digest(plan)
            or claims.intent_digest != plan.intent_digest
        ):
            raise PermitRejected(
                PermitRejectionCode.ACTION_MISMATCH,
                "permit is not bound to the supplied execution plan",
            )
        consumption = PermitConsumption(
            permit_id=claims.permit_id,
            action_digest=claims.action_digest,
            consumed_at=authorized_at,
        )
        self._consumption_store.consume(consumption)
        return ExecutionAuthorization(
            permit_id=claims.permit_id,
            document_id=claims.document_id,
            revision_digest=claims.revision_digest,
            action_digest=claims.action_digest,
            audience=claims.audience,
            authorized_at=authorized_at,
            expires_at=claims.expires_at,
        )
