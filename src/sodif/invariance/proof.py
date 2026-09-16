"""Create and verify field-level semantic evidence bound to an API action."""

from sodif.domain.canonical import sha256_digest
from sodif.domain.enums import ConsensusStatus, VerificationOutcomeStatus, ViewKind
from sodif.domain.invariance import (
    ExecutionFieldBinding,
    ExecutionProofBundle,
    FieldEvidenceReference,
    SemanticChallenge,
    SemanticInvarianceProof,
    StableFieldCommitment,
)
from sodif.domain.models import DocumentEnvelope, ExecutionPlan
from sodif.domain.schemas import IntentSchema
from sodif.domain.verification import AdaptiveVerificationOutcome
from sodif.invariance.errors import InvarianceRejected, InvarianceRejectionCode
from sodif.invariance.merkle import merkle_root
from sodif.verification.errors import SemanticNormalizationError
from sodif.verification.normalization import normalize_semantic_value


def _challenge_payload(challenge: SemanticChallenge) -> dict[str, object]:
    return {
        "document_id": challenge.document_id,
        "revision_digest": challenge.revision_digest,
        "policy_digest": challenge.policy_digest,
        "server_nonce_digest": challenge.server_nonce_digest,
        "selected_profiles": challenge.selected_profiles,
    }


def _field_payload(field: StableFieldCommitment) -> dict[str, object]:
    return {
        "name": field.name,
        "data_type": field.data_type,
        "value": field.value,
        "critical": field.critical,
        "evidence": field.evidence,
    }


def _binding_digest(binding: ExecutionFieldBinding) -> str:
    return sha256_digest(
        {
            "parameter_name": binding.parameter_name,
            "parameter_location": binding.parameter_location,
            "field_name": binding.field_name,
            "value_digest": binding.value_digest,
            "field_leaf_digest": binding.field_leaf_digest,
        }
    )


class SemanticInvarianceProver:
    """Prove unanimity across structural and human-visible evidence classes."""

    def prove(
        self,
        document: DocumentEnvelope,
        verification: AdaptiveVerificationOutcome,
        schema: IntentSchema,
        challenge: SemanticChallenge,
    ) -> SemanticInvarianceProof:
        consensus = verification.final_consensus
        if (
            verification.status is not VerificationOutcomeStatus.ACCEPTED
            or consensus is None
            or consensus.status is not ConsensusStatus.ACCEPTED
        ):
            raise InvarianceRejected(
                InvarianceRejectionCode.FIELD_NOT_STABLE,
                "semantic invariance requires an accepted verification outcome",
            )
        if (
            document.document_id != verification.document_id
            or document.revision_digest != verification.revision_digest
            or challenge.document_id != document.document_id
            or challenge.revision_digest != document.revision_digest
            or challenge.policy_digest != document.policy.digest
        ):
            raise InvarianceRejected(
                InvarianceRejectionCode.CONTEXT_MISMATCH,
                "document, verification and challenge do not describe the same revision",
            )

        views = {view.view_id: view for view in verification.views}
        definitions = {field.name: field for field in schema.fields}
        commitments: list[StableFieldCommitment] = []
        for field in sorted(consensus.fields, key=lambda item: item.name):
            if field.status is not ConsensusStatus.ACCEPTED:
                raise InvarianceRejected(
                    InvarianceRejectionCode.FIELD_NOT_STABLE,
                    f"field {field.name!r} is not semantically stable",
                )
            definition = definitions[field.name]
            evidence: list[FieldEvidenceReference] = []
            for view_id in field.supporting_views:
                try:
                    view = views[view_id]
                    semantic_field = next(item for item in view.fields if item.name == field.name)
                except (KeyError, StopIteration) as exc:
                    raise InvarianceRejected(
                        InvarianceRejectionCode.CONTEXT_MISMATCH,
                        f"field {field.name!r} references unavailable evidence",
                    ) from exc
                if view.adapter_id not in challenge.selected_profiles:
                    raise InvarianceRejected(
                        InvarianceRejectionCode.CHALLENGE_PROFILE_MISMATCH,
                        f"adapter {view.adapter_id!r} was not selected by the challenge",
                    )
                evidence.append(
                    FieldEvidenceReference(
                        view_id=view.view_id,
                        view_kind=view.kind,
                        adapter_id=view.adapter_id,
                        adapter_version=view.adapter_version,
                        locator=semantic_field.provenance.locator,
                        provenance_digest=semantic_field.provenance.source_digest,
                    )
                )
            kinds = {item.view_kind for item in evidence}
            if definition.critical and (
                ViewKind.STRUCTURAL not in kinds
                or not kinds.intersection({ViewKind.VISUAL, ViewKind.VISUAL_SECONDARY})
            ):
                raise InvarianceRejected(
                    InvarianceRejectionCode.EVIDENCE_CLASS_MISSING,
                    f"critical field {field.name!r} lacks structural or visual evidence",
                )
            evidence_tuple = tuple(evidence)
            payload = {
                "name": field.name,
                "data_type": field.data_type,
                "value": field.accepted_value,
                "critical": definition.critical,
                "evidence": evidence_tuple,
            }
            commitments.append(
                StableFieldCommitment(
                    name=field.name,
                    data_type=field.data_type,
                    value=field.accepted_value,
                    critical=definition.critical,
                    evidence=evidence_tuple,
                    leaf_digest=sha256_digest(payload),
                )
            )

        field_tuple = tuple(commitments)
        root = merkle_root(tuple(field.leaf_digest for field in field_tuple))
        identity = sha256_digest(
            {
                "document_id": document.document_id,
                "revision_digest": document.revision_digest,
                "schema_id": schema.schema_id,
                "schema_version": schema.version,
                "policy_digest": document.policy.digest,
                "challenge_digest": challenge.challenge_digest,
                "field_root": root,
            }
        )
        proof = SemanticInvarianceProof(
            proof_id=f"invariance-{identity[7:23]}",
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            schema_id=schema.schema_id,
            schema_version=schema.version,
            policy_digest=document.policy.digest,
            challenge=challenge,
            fields=field_tuple,
            field_root=root,
        )
        self.verify(proof)
        return proof

    def verify(self, proof: SemanticInvarianceProof) -> None:
        if sha256_digest(_challenge_payload(proof.challenge)) != proof.challenge.challenge_digest:
            raise InvarianceRejected(
                InvarianceRejectionCode.CONTEXT_MISMATCH,
                "semantic challenge digest is invalid",
            )
        for field in proof.fields:
            if sha256_digest(_field_payload(field)) != field.leaf_digest:
                raise InvarianceRejected(
                    InvarianceRejectionCode.FIELD_ROOT_MISMATCH,
                    f"field commitment {field.name!r} is invalid",
                )
        root = merkle_root(tuple(field.leaf_digest for field in proof.fields))
        if root != proof.field_root:
            raise InvarianceRejected(
                InvarianceRejectionCode.FIELD_ROOT_MISMATCH,
                "semantic field root does not match its commitments",
            )


class ExecutionProofService:
    """Bind every API parameter to one stable field and verify full coverage."""

    def bind(
        self,
        invariance: SemanticInvarianceProof,
        plan: ExecutionPlan,
    ) -> ExecutionProofBundle:
        SemanticInvarianceProver().verify(invariance)
        fields = {field.name: field for field in invariance.fields}
        bindings: list[ExecutionFieldBinding] = []
        for parameter in sorted(
            plan.parameters,
            key=lambda item: (item.location.value, item.name),
        ):
            field = fields.get(parameter.name)
            if field is None:
                raise InvarianceRejected(
                    InvarianceRejectionCode.PAYLOAD_COVERAGE_MISSING,
                    f"parameter {parameter.name!r} has no stable document field",
                )
            try:
                parameter_value = normalize_semantic_value(field.data_type, parameter.value)
                approved_value = normalize_semantic_value(field.data_type, field.value)
            except SemanticNormalizationError as exc:
                raise InvarianceRejected(
                    InvarianceRejectionCode.PAYLOAD_VALUE_MISMATCH,
                    f"parameter {parameter.name!r} cannot be normalized",
                ) from exc
            if parameter_value.comparison_key != approved_value.comparison_key:
                raise InvarianceRejected(
                    InvarianceRejectionCode.PAYLOAD_VALUE_MISMATCH,
                    f"parameter {parameter.name!r} differs from the stable document value",
                )
            bindings.append(
                ExecutionFieldBinding(
                    parameter_name=parameter.name,
                    parameter_location=parameter.location,
                    field_name=field.name,
                    value_digest=sha256_digest(
                        {
                            "field_name": field.name,
                            "value": parameter_value.canonical_value,
                        }
                    ),
                    field_leaf_digest=field.leaf_digest,
                )
            )
        binding_tuple = tuple(bindings)
        return ExecutionProofBundle(
            invariance=invariance,
            action_digest=sha256_digest(plan),
            bindings=binding_tuple,
            binding_root=merkle_root(tuple(_binding_digest(item) for item in binding_tuple)),
        )

    def verify(self, bundle: ExecutionProofBundle, plan: ExecutionPlan) -> None:
        if bundle.action_digest != sha256_digest(plan):
            raise InvarianceRejected(
                InvarianceRejectionCode.ACTION_MISMATCH,
                "execution proof is bound to another API action",
            )
        expected = self.bind(bundle.invariance, plan)
        if expected.bindings != bundle.bindings:
            raise InvarianceRejected(
                InvarianceRejectionCode.PAYLOAD_VALUE_MISMATCH,
                "execution field bindings differ from the supplied payload",
            )
        if expected.binding_root != bundle.binding_root:
            raise InvarianceRejected(
                InvarianceRejectionCode.BINDING_ROOT_MISMATCH,
                "execution binding root is invalid",
            )
