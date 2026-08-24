"""End-to-end tests for exact-action, one-time cryptographic permits."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from sodif.domain.canonical import sha256_digest
from sodif.domain.contracts import PermitAuthorizer, PermitIssuer
from sodif.domain.enums import (
    ConsensusStatus,
    HttpMethod,
    ParameterLocation,
    SemanticDataType,
    SignatureAlgorithm,
    VerificationLevel,
    VerificationOutcomeStatus,
    ViewKind,
)
from sodif.domain.models import (
    ActionParameter,
    ConsensusField,
    ConsensusResult,
    ExecutionPlan,
    FieldProvenance,
    IntentManifest,
    IntentValue,
    PolicyReference,
    RiskAssessment,
    SemanticField,
    SemanticView,
)
from sodif.domain.permits import ExecutionPermit, ExecutionPermitClaims, TrustedPermitKey
from sodif.domain.verification import AdaptiveVerificationOutcome, VerificationAttempt
from sodif.permits import (
    Ed25519PermitIssuer,
    ExecutionPermitAuthorizer,
    InMemoryPermitConsumptionStore,
    InMemoryPermitTrustStore,
    PermitIssuancePolicy,
    PermitRejected,
    PermitRejectionCode,
    PermitVerificationPolicy,
    encode_permit_public_key,
)

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


def digest(character: str) -> str:
    return f"sha256:{character * 64}"


@dataclass
class MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class FixedPermitIdSource:
    def new_id(self) -> str:
        return "permit-fixed-001"


def policy(character: str = "b") -> PolicyReference:
    return PolicyReference(policy_id="policy-01", version="v1", digest=digest(character))


def semantic_view(kind: ViewKind, character: str) -> SemanticView:
    adapter_id = f"adapter-{kind.value}"
    field = SemanticField(
        name="supplier_id",
        data_type=SemanticDataType.IDENTIFIER,
        value="SUP-01",
        confidence=Decimal("0.98"),
        provenance=FieldProvenance(
            view_kind=kind,
            adapter_id=adapter_id,
            adapter_version="v1",
            locator=f"{kind.value}:supplier_id",
            source_digest=digest(character),
        ),
    )
    return SemanticView(
        view_id=f"view-{kind.value}",
        document_id="doc-001",
        revision_digest=digest("a"),
        kind=kind,
        adapter_id=adapter_id,
        adapter_version="v1",
        fields=(field,),
    )


def consensus() -> ConsensusResult:
    return ConsensusResult(
        document_id="doc-001",
        revision_digest=digest("a"),
        status=ConsensusStatus.ACCEPTED,
        fields=(
            ConsensusField(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                status=ConsensusStatus.ACCEPTED,
                accepted_value="SUP-01",
                supporting_views=("view-structural", "view-visual"),
            ),
        ),
    )


def accepted_verification() -> AdaptiveVerificationOutcome:
    result = consensus()
    views = (
        semantic_view(ViewKind.STRUCTURAL, "c"),
        semantic_view(ViewKind.VISUAL, "d"),
    )
    attempt = VerificationAttempt(
        level=VerificationLevel.V1_TARGETED,
        adapters_added=("adapter-structural", "adapter-visual"),
        view_ids_evaluated=tuple(view.view_id for view in views),
        incremental_cost_units=4,
        consensus=result,
    )
    return AdaptiveVerificationOutcome(
        document_id="doc-001",
        revision_digest=digest("a"),
        status=VerificationOutcomeStatus.ACCEPTED,
        initial_level=VerificationLevel.V1_TARGETED,
        final_level=VerificationLevel.V1_TARGETED,
        risk=RiskAssessment(
            score=Decimal("10"),
            verification_level=VerificationLevel.V1_TARGETED,
            policy=policy(),
        ),
        views=views,
        attempts=(attempt,),
        final_consensus=result,
        total_cost_units=4,
        available_cost_units=6,
        reasons=("semantic-consensus-accepted",),
    )


def manifest(manifest_policy: PolicyReference | None = None) -> IntentManifest:
    return IntentManifest(
        manifest_id="manifest-001",
        document_id="doc-001",
        revision_digest=digest("a"),
        schema_id="purchase-order",
        schema_version="v1",
        action_type="create-purchase-order",
        policy=manifest_policy or policy(),
        fields=(
            IntentValue(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                value="SUP-01",
                source_views=("view-structural", "view-visual"),
                provenance_digests=(digest("c"), digest("d")),
            ),
        ),
    )


def plan(source_manifest: IntentManifest, path: str = "/purchase-orders") -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="plan-001",
        intent_digest=sha256_digest(source_manifest),
        method=HttpMethod.POST,
        path=path,
        audience="erp-api",
        parameters=(
            ActionParameter(
                name="supplier_id",
                location=ParameterLocation.BODY,
                value="SUP-01",
            ),
        ),
    )


def private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes(range(65, 97)))


def issuer(
    clock: MutableClock,
    issuance_policy: PermitIssuancePolicy | None = None,
) -> Ed25519PermitIssuer:
    return Ed25519PermitIssuer(
        "sodif-permit-issuer",
        "permit-key-01",
        private_key(),
        clock,
        FixedPermitIdSource(),
        issuance_policy,
    )


def trusted_key(**updates: object) -> TrustedPermitKey:
    source = private_key().public_key()
    base: dict[str, object] = {
        "key_id": "permit-key-01",
        "issuer_id": "sodif-permit-issuer",
        "algorithm": SignatureAlgorithm.ED25519,
        "public_key": encode_permit_public_key(source),
        "active_from": NOW - timedelta(days=1),
    }
    return TrustedPermitKey.model_validate({**base, **updates})


def issued_permit(clock: MutableClock, ttl: timedelta | None = None) -> tuple[
    ExecutionPermit, ExecutionPlan
]:
    source_manifest = manifest()
    execution_plan = plan(source_manifest)
    permit = issuer(clock).issue(
        accepted_verification(),
        source_manifest,
        execution_plan,
        ttl,
    )
    return permit, execution_plan


def authorizer(
    clock: MutableClock,
    store: InMemoryPermitConsumptionStore | None = None,
    key: TrustedPermitKey | None = None,
    verification_policy: PermitVerificationPolicy | None = None,
) -> ExecutionPermitAuthorizer:
    return ExecutionPermitAuthorizer(
        InMemoryPermitTrustStore((key or trusted_key(),)),
        store or InMemoryPermitConsumptionStore(),
        clock,
        verification_policy,
    )


def test_issuer_binds_all_approved_artifacts_into_signed_claims() -> None:
    clock = MutableClock(NOW)
    source_manifest = manifest()
    execution_plan = plan(source_manifest)
    verification = accepted_verification()
    permit_issuer = issuer(clock)

    permit = permit_issuer.issue(verification, source_manifest, execution_plan)

    assert isinstance(permit_issuer, PermitIssuer)
    assert permit.claims.protocol == "sodif.execution-permit/v1"
    assert permit.claims.verification_digest == sha256_digest(verification)
    assert permit.claims.consensus_digest == sha256_digest(verification.final_consensus)
    assert permit.claims.intent_digest == sha256_digest(source_manifest)
    assert permit.claims.action_digest == sha256_digest(execution_plan)
    assert permit.claims.expires_at - permit.claims.issued_at == timedelta(seconds=60)


def test_issuer_rejects_nonaccepted_or_mismatched_inputs() -> None:
    clock = MutableClock(NOW)
    permit_issuer = issuer(clock)
    source_manifest = manifest()
    execution_plan = plan(source_manifest)
    verification = accepted_verification()

    invalid_cases = (
        (
            verification.model_copy(update={"status": VerificationOutcomeStatus.ESCALATED}),
            source_manifest,
            execution_plan,
            PermitRejectionCode.VERIFICATION_NOT_ACCEPTED,
        ),
        (
            verification,
            source_manifest.model_copy(update={"document_id": "doc-002"}),
            execution_plan,
            PermitRejectionCode.CONTEXT_MISMATCH,
        ),
        (
            verification,
            source_manifest,
            execution_plan.model_copy(update={"intent_digest": digest("e")}),
            PermitRejectionCode.INTENT_MISMATCH,
        ),
    )
    for current_verification, current_manifest, current_plan, expected_code in invalid_cases:
        with pytest.raises(PermitRejected) as captured:
            permit_issuer.issue(current_verification, current_manifest, current_plan)
        assert captured.value.code is expected_code


def test_issuer_rejects_policy_mismatch_and_unsafe_ttl() -> None:
    clock = MutableClock(NOW)
    permit_issuer = issuer(clock)
    mismatched_manifest = manifest(policy("e"))

    with pytest.raises(PermitRejected) as mismatch:
        permit_issuer.issue(
            accepted_verification(),
            mismatched_manifest,
            plan(mismatched_manifest),
        )
    with pytest.raises(PermitRejected) as ttl:
        permit_issuer.issue(
            accepted_verification(),
            manifest(),
            plan(manifest()),
            timedelta(minutes=3),
        )

    assert mismatch.value.code is PermitRejectionCode.POLICY_MISMATCH
    assert ttl.value.code is PermitRejectionCode.TTL_INVALID


def test_authorization_consumes_valid_permit_exactly_once() -> None:
    clock = MutableClock(NOW)
    permit, execution_plan = issued_permit(clock)
    store = InMemoryPermitConsumptionStore()
    permit_authorizer = authorizer(clock, store)

    authorization = permit_authorizer.authorize(permit, execution_plan, "erp-api")
    with pytest.raises(PermitRejected) as replay:
        permit_authorizer.authorize(permit, execution_plan, "erp-api")

    assert isinstance(permit_authorizer, PermitAuthorizer)
    assert authorization.permit_id == permit.claims.permit_id
    assert store.get(permit.claims.permit_id) is not None
    assert replay.value.code is PermitRejectionCode.PERMIT_REPLAYED


def test_authorizer_rejects_other_action_or_audience_without_consuming() -> None:
    clock = MutableClock(NOW)
    permit, execution_plan = issued_permit(clock)
    store = InMemoryPermitConsumptionStore()
    permit_authorizer = authorizer(clock, store)

    with pytest.raises(PermitRejected) as changed_action:
        permit_authorizer.authorize(
            permit,
            execution_plan.model_copy(update={"path": "/other-orders"}),
            "erp-api",
        )
    with pytest.raises(PermitRejected) as audience:
        permit_authorizer.authorize(permit, execution_plan, "other-api")

    assert changed_action.value.code is PermitRejectionCode.ACTION_MISMATCH
    assert audience.value.code is PermitRejectionCode.AUDIENCE_MISMATCH
    assert store.get(permit.claims.permit_id) is None


def test_tampered_or_untrusted_permit_is_rejected() -> None:
    clock = MutableClock(NOW)
    permit, execution_plan = issued_permit(clock)
    tampered = ExecutionPermit(
        claims=permit.claims.model_copy(update={"audience": "other-api"}),
        signature=permit.signature,
    )

    with pytest.raises(PermitRejected) as changed:
        authorizer(clock).authorize(tampered, execution_plan, "other-api")
    with pytest.raises(PermitRejected) as unknown:
        ExecutionPermitAuthorizer(
            InMemoryPermitTrustStore(()),
            InMemoryPermitConsumptionStore(),
            clock,
        ).authorize(permit, execution_plan, "erp-api")

    assert changed.value.code is PermitRejectionCode.SIGNATURE_INVALID
    assert unknown.value.code is PermitRejectionCode.UNTRUSTED_ISSUER_KEY


@pytest.mark.parametrize(
    ("key_updates", "code"),
    [
        ({"issuer_id": "other-issuer"}, PermitRejectionCode.ISSUER_KEY_MISMATCH),
        ({"active_from": NOW + timedelta(seconds=1)}, PermitRejectionCode.KEY_NOT_ACTIVE),
        ({"revoked_at": NOW}, PermitRejectionCode.KEY_REVOKED),
    ],
)
def test_issuer_key_lifecycle_is_enforced(
    key_updates: dict[str, object],
    code: PermitRejectionCode,
) -> None:
    clock = MutableClock(NOW)
    permit, execution_plan = issued_permit(clock)

    with pytest.raises(PermitRejected) as captured:
        authorizer(clock, key=trusted_key(**key_updates)).authorize(
            permit,
            execution_plan,
            "erp-api",
        )

    assert captured.value.code is code


def test_permit_time_window_and_verifier_ttl_are_enforced() -> None:
    clock = MutableClock(NOW)
    permit, execution_plan = issued_permit(clock, timedelta(seconds=90))

    clock.current = NOW - timedelta(seconds=1)
    with pytest.raises(PermitRejected) as future:
        authorizer(clock).authorize(permit, execution_plan, "erp-api")
    clock.current = permit.claims.expires_at
    with pytest.raises(PermitRejected) as expired:
        authorizer(clock).authorize(permit, execution_plan, "erp-api")
    clock.current = NOW
    with pytest.raises(PermitRejected) as ttl:
        authorizer(
            clock,
            verification_policy=PermitVerificationPolicy(maximum_ttl=timedelta(seconds=60)),
        ).authorize(permit, execution_plan, "erp-api")

    assert future.value.code is PermitRejectionCode.PERMIT_NOT_YET_VALID
    assert expired.value.code is PermitRejectionCode.PERMIT_EXPIRED
    assert ttl.value.code is PermitRejectionCode.TTL_INVALID


def test_atomic_consumption_allows_exactly_one_concurrent_authorization() -> None:
    clock = MutableClock(NOW)
    permit, execution_plan = issued_permit(clock)
    store = InMemoryPermitConsumptionStore()
    permit_authorizer = authorizer(clock, store)

    def attempt() -> str:
        try:
            permit_authorizer.authorize(permit, execution_plan, "erp-api")
            return "authorized"
        except PermitRejected as exc:
            return exc.code.value

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: attempt(), range(16)))

    assert results.count("authorized") == 1
    assert results.count(PermitRejectionCode.PERMIT_REPLAYED.value) == 15


def test_permit_model_and_policy_invariants_fail_early() -> None:
    base_claims = {
        "permit_id": "permit-001",
        "issuer_id": "issuer-01",
        "key_id": "key-01",
        "algorithm": SignatureAlgorithm.ED25519,
        "document_id": "doc-001",
        "revision_digest": digest("a"),
        "verification_digest": digest("b"),
        "consensus_digest": digest("c"),
        "intent_digest": digest("d"),
        "action_digest": digest("e"),
        "policy_digest": digest("f"),
        "audience": "erp-api",
        "issued_at": NOW,
        "expires_at": NOW,
    }

    with pytest.raises(ValidationError, match="after issued_at"):
        ExecutionPermitClaims.model_validate(base_claims)
    with pytest.raises(ValidationError, match="active_until"):
        TrustedPermitKey.model_validate(
            {
                "key_id": "key-01",
                "issuer_id": "issuer-01",
                "algorithm": SignatureAlgorithm.ED25519,
                "public_key": "A" * 43,
                "active_from": NOW,
                "active_until": NOW,
            }
        )
    with pytest.raises(ValueError, match="default permit TTL"):
        PermitIssuancePolicy(
            default_ttl=timedelta(minutes=3),
            maximum_ttl=timedelta(minutes=2),
        )
    with pytest.raises(ValueError, match="positive"):
        PermitVerificationPolicy(maximum_ttl=timedelta(0))
