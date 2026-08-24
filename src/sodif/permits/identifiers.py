"""Replaceable cryptographically random permit identifiers."""

from secrets import token_hex
from typing import Protocol, runtime_checkable

from sodif.domain.types import Identifier


@runtime_checkable
class PermitIdSource(Protocol):
    def new_id(self) -> Identifier: ...


class SecretsPermitIdSource:
    def new_id(self) -> Identifier:
        return f"permit-{token_hex(16)}"
