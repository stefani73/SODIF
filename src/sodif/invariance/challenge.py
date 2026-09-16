"""Post-signature deterministic challenges with an unpredictable server nonce."""

from dataclasses import dataclass

from sodif.domain.canonical import sha256_bytes, sha256_digest
from sodif.domain.invariance import SemanticChallenge
from sodif.domain.models import DocumentEnvelope
from sodif.domain.types import Identifier


@dataclass(frozen=True, slots=True)
class ChallengePolicy:
    structural_profile: Identifier = "pypdf-structural-v1"
    visual_profiles: tuple[Identifier, Identifier] = (
        "mupdf-tesseract-300-psm6-v1",
        "poppler-tesseract-360-psm11-v1",
    )

    def __post_init__(self) -> None:
        profiles = (self.structural_profile, *self.visual_profiles)
        if len(profiles) != len(set(profiles)):
            raise ValueError("challenge profiles must be unique")


class SemanticChallengeGenerator:
    def __init__(self, policy: ChallengePolicy | None = None) -> None:
        self._policy = policy or ChallengePolicy()

    def generate(self, document: DocumentEnvelope, server_nonce: bytes) -> SemanticChallenge:
        if len(server_nonce) < 16:
            raise ValueError("semantic challenge nonce requires at least 128 bits")
        nonce_digest = sha256_bytes(server_nonce)
        seed = sha256_digest(
            {
                "document_id": document.document_id,
                "revision_digest": document.revision_digest,
                "policy_digest": document.policy.digest,
                "signature_evidence": document.signatures,
                "server_nonce_digest": nonce_digest,
            }
        )
        visual = self._policy.visual_profiles
        if int(seed[-1], 16) % 2:
            visual = (visual[1], visual[0])
        selected = (self._policy.structural_profile, *visual)
        challenge_digest = sha256_digest(
            {
                "document_id": document.document_id,
                "revision_digest": document.revision_digest,
                "policy_digest": document.policy.digest,
                "server_nonce_digest": nonce_digest,
                "selected_profiles": selected,
            }
        )
        return SemanticChallenge(
            challenge_id=f"challenge-{challenge_digest[7:23]}",
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            policy_digest=document.policy.digest,
            server_nonce_digest=nonce_digest,
            selected_profiles=selected,
            challenge_digest=challenge_digest,
        )
