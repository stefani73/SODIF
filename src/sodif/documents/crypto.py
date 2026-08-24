"""Ed25519 signing and verification for the SODIF revision envelope."""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as Base64Error
from datetime import datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from sodif.documents.errors import DocumentRejected, DocumentRejectionCode
from sodif.domain.canonical import canonical_bytes, sha256_bytes
from sodif.domain.enums import SignatureAlgorithm, SignatureStatus
from sodif.domain.models import SignatureEvidence
from sodif.domain.revisions import (
    SignedRevision,
    SignedRevisionMetadata,
    TrustedSignerKey,
)
from sodif.domain.types import Digest, Identifier


def _encode_unpadded(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_unpadded(value: str, expected_size: int) -> bytes:
    try:
        decoded = urlsafe_b64decode(f"{value}{'=' * (-len(value) % 4)}")
    except (Base64Error, ValueError) as exc:
        raise DocumentRejected(
            DocumentRejectionCode.SIGNATURE_INVALID,
            "signature encoding is invalid",
        ) from exc
    if len(decoded) != expected_size:
        raise DocumentRejected(
            DocumentRejectionCode.SIGNATURE_INVALID,
            "signature has an invalid byte length",
        )
    return decoded


def encode_public_key(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return _encode_unpadded(raw)


class InMemoryTrustStore:
    """Read-only local trust registry replaceable by HSM/PKI adapters later."""

    def __init__(self, keys: tuple[TrustedSignerKey, ...]) -> None:
        keyed = {key.key_id: key for key in keys}
        if len(keyed) != len(keys):
            raise ValueError("trusted key identifiers must be unique")
        self._keys = keyed

    def resolve(self, key_id: Identifier) -> TrustedSignerKey:
        try:
            return self._keys[key_id]
        except KeyError as exc:
            raise DocumentRejected(
                DocumentRejectionCode.UNTRUSTED_KEY,
                f"key {key_id!r} is not trusted",
            ) from exc


class Ed25519RevisionSigner:
    """Deterministic envelope signer used by fixtures and demo scenarios."""

    def __init__(
        self,
        signer_id: Identifier,
        key_id: Identifier,
        private_key: Ed25519PrivateKey,
    ) -> None:
        self.signer_id = signer_id
        self.key_id = key_id
        self._private_key = private_key

    def public_key(self) -> Ed25519PublicKey:
        return self._private_key.public_key()

    def sign(self, metadata: SignedRevisionMetadata) -> SignedRevision:
        if metadata.signer_id != self.signer_id or metadata.key_id != self.key_id:
            raise ValueError("metadata does not match the configured signer")
        if metadata.algorithm is not SignatureAlgorithm.ED25519:
            raise ValueError("signer supports only Ed25519")
        raw_signature = self._private_key.sign(canonical_bytes(metadata))
        return SignedRevision(metadata=metadata, signature=_encode_unpadded(raw_signature))


def verify_revision_signature(
    revision: SignedRevision,
    trust_store: InMemoryTrustStore,
    validated_at: datetime,
    *,
    validator_id: Identifier = "sodif-ed25519-validator",
    validator_version: Identifier = "v1",
) -> tuple[SignatureEvidence, Digest]:
    """Verify trust, key lifecycle and detached signature over canonical metadata."""
    metadata = revision.metadata
    key = trust_store.resolve(metadata.key_id)
    if key.signer_id != metadata.signer_id or key.algorithm is not metadata.algorithm:
        raise DocumentRejected(
            DocumentRejectionCode.SIGNER_KEY_MISMATCH,
            "trusted key is not bound to the declared signer and algorithm",
        )
    if metadata.signed_at > validated_at:
        raise DocumentRejected(
            DocumentRejectionCode.SIGNING_TIME_INVALID,
            "document signing time is in the future",
        )
    if metadata.signed_at < key.active_from or (
        key.active_until is not None and metadata.signed_at >= key.active_until
    ):
        raise DocumentRejected(
            DocumentRejectionCode.KEY_NOT_ACTIVE,
            "key was not active at document signing time",
        )
    if key.revoked_at is not None and metadata.signed_at >= key.revoked_at:
        raise DocumentRejected(
            DocumentRejectionCode.KEY_REVOKED,
            "key was revoked at document signing time",
        )

    raw_signature = _decode_unpadded(revision.signature, expected_size=64)
    raw_public_key = _decode_unpadded(key.public_key, expected_size=32)
    try:
        Ed25519PublicKey.from_public_bytes(raw_public_key).verify(
            raw_signature,
            canonical_bytes(metadata),
        )
    except (InvalidSignature, ValueError) as exc:
        raise DocumentRejected(
            DocumentRejectionCode.SIGNATURE_INVALID,
            "detached signature does not cover the declared revision",
        ) from exc

    evidence = SignatureEvidence(
        signer_id=metadata.signer_id,
        status=SignatureStatus.VALID,
        covers_revision=True,
        validated_at=validated_at,
        validator_id=validator_id,
        validator_version=validator_version,
    )
    return evidence, sha256_bytes(raw_signature)
