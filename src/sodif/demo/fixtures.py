"""Small deterministic artifact and schema catalog for the TRL 4 flight."""

from decimal import Decimal

from sodif.demo.adapters import ScenarioValue
from sodif.domain.enums import HttpMethod, SemanticDataType
from sodif.domain.models import ActionContext, PolicyReference
from sodif.domain.schemas import IntentFieldDefinition, IntentSchema

BASE_PDF = (
    b"%PDF-1.7\n"
    b"1 0 obj\n<</Type/Catalog/SODIF(Demo Purchase Order)>>\nendobj\n"
    b"% supplier_id=SUP-01;total_amount=1250.00;currency=EUR\n"
    b"%%EOF\n"
)
TAMPERED_PDF = BASE_PDF.replace(b"1250.00", b"9250.00")


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


def purchase_order_action() -> ActionContext:
    return ActionContext(
        action_type="create-purchase-order",
        method=HttpMethod.POST,
        path="/purchase-orders",
        audience="erp-purchase-api",
    )


def accepted_values(amount: Decimal = Decimal("1250.00")) -> dict[str, ScenarioValue]:
    return {
        "supplier_id": (SemanticDataType.IDENTIFIER, "SUP-01"),
        "total_amount": (SemanticDataType.DECIMAL, amount),
        "currency": (SemanticDataType.CURRENCY, "EUR"),
    }
