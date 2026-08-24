"""Stable policy reference used by local signed-document ingestion."""

from sodif.domain.models import PolicyReference


def ingestion_policy() -> PolicyReference:
    """Return the explicit policy bound to locally ingested archive records."""
    return PolicyReference(
        policy_id="flight-policy",
        version="v1",
        digest=f"sha256:{'b' * 64}",
    )
