"""Deterministic evidence fixture for gateway workspaces and unit tests."""

from decimal import Decimal

from sodif.domain.canonical import sha256_digest
from sodif.domain.enums import SemanticDataType, ViewKind
from sodif.domain.invariance import (
    ExecutionProofBundle,
    FieldEvidenceReference,
    SemanticChallenge,
    SemanticInvarianceProof,
    StableFieldCommitment,
)
from sodif.domain.models import ExecutionPlan
from sodif.domain.types import Digest
from sodif.invariance.merkle import merkle_root
from sodif.invariance.proof import ExecutionProofService


def _infer_type(value: object) -> SemanticDataType:
    if isinstance(value, bool):
        return SemanticDataType.BOOLEAN
    if isinstance(value, int):
        return SemanticDataType.INTEGER
    if isinstance(value, Decimal):
        return SemanticDataType.DECIMAL
    if isinstance(value, str) and len(value) == 3 and value.isalpha():
        return SemanticDataType.CURRENCY
    return SemanticDataType.IDENTIFIER


def sample_execution_proof(
    plan: ExecutionPlan,
    *,
    document_id: str = "doc-001",
    revision_digest: Digest = f"sha256:{'a' * 64}",
    policy_digest: Digest = f"sha256:{'e' * 64}",
    schema_id: str = "purchase-order",
    schema_version: str = "v1",
) -> ExecutionProofBundle:
    selected_profiles = (
        "pypdf-structural-v1",
        "mupdf-tesseract-300-psm6-v1",
        "poppler-tesseract-360-psm11-v1",
    )
    challenge_payload = {
        "document_id": document_id,
        "revision_digest": revision_digest,
        "policy_digest": policy_digest,
        "server_nonce_digest": f"sha256:{'f' * 64}",
        "selected_profiles": selected_profiles,
    }
    challenge = SemanticChallenge(
        challenge_id="challenge-sample",
        document_id=document_id,
        revision_digest=revision_digest,
        policy_digest=policy_digest,
        server_nonce_digest=f"sha256:{'f' * 64}",
        selected_profiles=selected_profiles,
        challenge_digest=sha256_digest(challenge_payload),
    )
    fields: list[StableFieldCommitment] = []
    for parameter in sorted(plan.parameters, key=lambda item: item.name):
        data_type = _infer_type(parameter.value)
        evidence = (
            FieldEvidenceReference(
                view_id=f"view-structural-{parameter.name}",
                view_kind=ViewKind.STRUCTURAL,
                adapter_id=selected_profiles[0],
                adapter_version="v1",
                locator=f"page=1;field={parameter.name}",
                provenance_digest=sha256_digest(
                    {"profile": selected_profiles[0], "field": parameter.name}
                ),
            ),
            FieldEvidenceReference(
                view_id=f"view-visual-{parameter.name}",
                view_kind=ViewKind.VISUAL,
                adapter_id=selected_profiles[1],
                adapter_version="v1",
                locator=f"page=1;visual_field={parameter.name}",
                provenance_digest=sha256_digest(
                    {"profile": selected_profiles[1], "field": parameter.name}
                ),
            ),
        )
        payload = {
            "name": parameter.name,
            "data_type": data_type,
            "value": parameter.value,
            "critical": parameter.name != "currency",
            "evidence": evidence,
        }
        fields.append(
            StableFieldCommitment(
                name=parameter.name,
                data_type=data_type,
                value=parameter.value,
                critical=parameter.name != "currency",
                evidence=evidence,
                leaf_digest=sha256_digest(payload),
            )
        )
    field_tuple = tuple(fields)
    field_root = merkle_root(tuple(field.leaf_digest for field in field_tuple))
    invariance = SemanticInvarianceProof(
        proof_id="invariance-sample",
        document_id=document_id,
        revision_digest=revision_digest,
        schema_id=schema_id,
        schema_version=schema_version,
        policy_digest=policy_digest,
        challenge=challenge,
        fields=field_tuple,
        field_root=field_root,
    )
    return ExecutionProofService().bind(invariance, plan)
