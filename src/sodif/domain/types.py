"""Reusable constrained types for the SODIF domain."""

from decimal import Decimal
from typing import Annotated, TypeAlias

from pydantic import Field, StringConstraints

Digest: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$"),
]
Identifier: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$"),
]
FieldName: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$"),
]
Confidence: TypeAlias = Annotated[Decimal, Field(ge=Decimal("0"), le=Decimal("1"))]
RiskScore: TypeAlias = Annotated[Decimal, Field(ge=Decimal("0"), le=Decimal("100"))]
JsonScalar: TypeAlias = str | int | bool | Decimal | None

