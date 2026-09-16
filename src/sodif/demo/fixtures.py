"""Real PDF artifacts and schema catalog for the TRL 4 flight."""

from decimal import Decimal
from io import BytesIO
from typing import Any, cast

import pymupdf
from PIL import Image, ImageDraw, ImageFont

from sodif.demo.adapters import ScenarioValue
from sodif.domain.enums import HttpMethod, SemanticDataType
from sodif.domain.models import ActionContext, PolicyReference
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema


def _pdf_bytes(values: dict[str, str]) -> bytes:
    document: Any = pymupdf.open()  # type: ignore[no-untyped-call]
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 90), "SODIF PURCHASE ORDER", fontsize=18)
    page.insert_text((72, 145), f"supplier id: {values['supplier_id']}", fontsize=14)
    page.insert_text((72, 180), f"total amount: {values['total_amount']}", fontsize=14)
    page.insert_text((72, 215), f"currency: {values['currency']}", fontsize=14)
    result = cast(
        bytes,
        document.tobytes(garbage=4, deflate=True, clean=True, no_new_id=True),
    )
    document.close()
    return result


def _split_representation_pdf() -> bytes:
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    try:
        title_font: ImageFont.FreeTypeFont | ImageFont.ImageFont = ImageFont.truetype(
            r"C:\Windows\Fonts\arialbd.ttf", 54
        )
        body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont = ImageFont.truetype(
            r"C:\Windows\Fonts\arial.ttf", 44
        )
    except OSError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    draw.text((120, 90), "SODIF PURCHASE ORDER", fill="black", font=title_font)
    draw.text((120, 250), "supplier id: SUP-01", fill="black", font=body_font)
    draw.text((120, 360), "total amount: 1250.00", fill="black", font=body_font)
    draw.text((120, 470), "currency: EUR", fill="black", font=body_font)
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")

    document: Any = pymupdf.open()  # type: ignore[no-untyped-call]
    page = document.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=image_bytes.getvalue())
    page.insert_text((72, 700), "supplier_id: SUP-01", fontsize=12, render_mode=3)
    page.insert_text((72, 720), "total_amount: 9250.00", fontsize=12, render_mode=3)
    page.insert_text((72, 740), "currency: EUR", fontsize=12, render_mode=3)
    result = cast(
        bytes,
        document.tobytes(garbage=4, deflate=True, clean=True, no_new_id=True),
    )
    document.close()
    return result


BASE_PDF = _pdf_bytes(
    {"supplier_id": "SUP-01", "total_amount": "1250.00", "currency": "EUR"}
)
TAMPERED_PDF = _pdf_bytes(
    {"supplier_id": "SUP-01", "total_amount": "9250.00", "currency": "EUR"}
)
REVISED_PDF = _pdf_bytes(
    {"supplier_id": "SUP-01", "total_amount": "1350.00", "currency": "EUR"}
)
SEMANTIC_SPLIT_PDF = _split_representation_pdf()


def flight_policy() -> PolicyReference:
    return PolicyReference(
        policy_id="flight-policy",
        version="v1",
        digest=f"sha256:{'b' * 64}",
    )


def purchase_order_schema() -> IntentSchema:
    return IntentSchema(
        schema_id="purchase-order",
        version="v1",
        action_type="create-purchase-order",
        fields=(
            IntentFieldDefinition(
                name="supplier_id",
                data_type=SemanticDataType.IDENTIFIER,
                description="Supplier identifier",
            ),
            IntentFieldDefinition(
                name="total_amount",
                data_type=SemanticDataType.DECIMAL,
                description="Approved order total",
            ),
            IntentFieldDefinition(
                name="currency",
                data_type=SemanticDataType.CURRENCY,
                required=False,
                critical=False,
                description="Order currency",
            ),
        ),
    )


def purchase_order_action(
    *,
    audience: str = "erp-purchase-api",
    path: str = "/purchase-orders",
) -> ActionContext:
    return ActionContext(
        action_type="create-purchase-order",
        method=HttpMethod.POST,
        path=path,
        audience=audience,
    )


def accepted_values(amount: Decimal = Decimal("1250.00")) -> dict[str, ScenarioValue]:
    return {
        "supplier_id": (SemanticDataType.IDENTIFIER, "SUP-01"),
        "total_amount": (SemanticDataType.DECIMAL, amount),
        "currency": (SemanticDataType.CURRENCY, "EUR"),
    }
