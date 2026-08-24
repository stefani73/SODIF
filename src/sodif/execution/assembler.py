"""Build a traceable intent manifest from accepted consensus."""

from sodif.domain.canonical import sha256_digest
from sodif.domain.enums import ConsensusStatus
from sodif.domain.models import (
    ConsensusResult,
    DocumentEnvelope,
    IntentManifest,
    IntentValue,
    PolicyReference,
)
from sodif.domain.schemas import IntentSchema, validate_manifest
from sodif.execution.errors import ExecutionRejected


class ConsensusIntentAssembler:
    def assemble(
        self,
        document: DocumentEnvelope,
        consensus: ConsensusResult,
        schema: IntentSchema,
        policy: PolicyReference,
    ) -> IntentManifest:
        if consensus.status is not ConsensusStatus.ACCEPTED:
            raise ExecutionRejected("intent requires accepted semantic consensus")
        if (
            document.document_id != consensus.document_id
            or document.revision_digest != consensus.revision_digest
        ):
            raise ExecutionRejected("document and consensus revision differ")
        if document.policy != policy:
            raise ExecutionRejected("document and intent policy differ")

        fields: list[IntentValue] = []
        for field in consensus.fields:
            if field.status is not ConsensusStatus.ACCEPTED:
                continue
            provenance_by_view = {
                candidate.view_id: candidate.provenance_digest for candidate in field.candidates
            }
            try:
                provenance = tuple(
                    provenance_by_view[view_id] for view_id in field.supporting_views
                )
            except KeyError as exc:
                raise ExecutionRejected("consensus support lacks provenance") from exc
            fields.append(
                IntentValue(
                    name=field.name,
                    data_type=field.data_type,
                    value=field.accepted_value,
                    source_views=field.supporting_views,
                    provenance_digests=provenance,
                )
            )
        if not fields:
            raise ExecutionRejected("accepted consensus contains no executable fields")
        identity_digest = sha256_digest(
            {
                "document_id": document.document_id,
                "revision_digest": document.revision_digest,
                "schema_id": schema.schema_id,
                "schema_version": schema.version,
                "action_type": schema.action_type,
                "fields": fields,
            }
        )
        manifest = IntentManifest(
            manifest_id=f"manifest-{identity_digest[7:23]}",
            document_id=document.document_id,
            revision_digest=document.revision_digest,
            schema_id=schema.schema_id,
            schema_version=schema.version,
            action_type=schema.action_type,
            policy=policy,
            fields=tuple(fields),
        )
        validation = validate_manifest(manifest, schema)
        if not validation.valid:
            codes = ", ".join(item.code for item in validation.violations)
            raise ExecutionRejected(f"assembled intent violates schema: {codes}")
        return manifest
