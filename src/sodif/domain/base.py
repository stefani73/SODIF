"""Shared configuration for immutable domain objects."""

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Strict, immutable and forward-compatible base for domain contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
    )

