"""Tests for independent structural and rendered PDF interpretations."""

from datetime import UTC, datetime

from sodif.demo.fixtures import (
    BASE_PDF,
    SEMANTIC_SPLIT_PDF,
    flight_policy,
    purchase_order_schema,
)
from sodif.domain.canonical import sha256_bytes
from sodif.domain.enums import DocumentFormat, SignatureStatus, ViewKind
from sodif.domain.models import DocumentEnvelope, SignatureEvidence
from sodif.extraction import challenged_pdf_adapters
from sodif.invariance import SemanticChallengeGenerator


def envelope(content: bytes, document_id: str = "doc-pdf-001") -> DocumentEnvelope:
    return DocumentEnvelope(
        document_id=document_id,
        format=DocumentFormat.PDF,
        revision_digest=sha256_bytes(content),
        signatures=(
            SignatureEvidence(
                signer_id="signer-01",
                status=SignatureStatus.VALID,
                covers_revision=True,
                validated_at=datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
                validator_id="validator-01",
                validator_version="v1",
            ),
        ),
        policy=flight_policy(),
        ingested_at=datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
    )


def values(view: object) -> dict[str, object]:
    return {field.name: field.value for field in view.fields}  # type: ignore[attr-defined]


def test_real_pdf_is_read_consistently_by_structural_and_visual_paths() -> None:
    document = envelope(BASE_PDF)
    challenge = SemanticChallengeGenerator().generate(document, bytes(range(32)))
    adapters = challenged_pdf_adapters(challenge)

    views = tuple(
        adapter.extract(document, BASE_PDF, purchase_order_schema()) for adapter in adapters
    )

    assert [view.kind for view in views] == [
        ViewKind.STRUCTURAL,
        ViewKind.VISUAL,
        ViewKind.VISUAL_SECONDARY,
    ]
    assert all(values(view)["supplier_id"] == "ACME-42" for view in views)
    assert all(values(view)["total_amount"] == "1250.00" for view in views)
    assert all(values(view)["currency"] == "EUR" for view in views)
    assert all("page=1" in field.provenance.locator for view in views for field in view.fields)


def test_hidden_pdf_text_cannot_override_the_human_visible_amount() -> None:
    document = envelope(SEMANTIC_SPLIT_PDF, "doc-pdf-split")
    challenge = SemanticChallengeGenerator().generate(document, bytes(range(32, 64)))
    structural, visual, secondary = challenged_pdf_adapters(challenge)

    structural_values = values(
        structural.extract(document, SEMANTIC_SPLIT_PDF, purchase_order_schema())
    )
    visual_values = values(visual.extract(document, SEMANTIC_SPLIT_PDF, purchase_order_schema()))
    secondary_values = values(
        secondary.extract(document, SEMANTIC_SPLIT_PDF, purchase_order_schema())
    )

    assert structural_values["total_amount"] == "9250.00"
    assert visual_values["total_amount"] == "1250.00"
    assert secondary_values["total_amount"] == "1250.00"
