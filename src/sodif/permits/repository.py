"""Atomic one-time permit consumption."""

from threading import RLock
from typing import Protocol, runtime_checkable

from sodif.domain.permits import PermitConsumption
from sodif.domain.types import Identifier
from sodif.permits.errors import PermitRejected, PermitRejectionCode


@runtime_checkable
class PermitConsumptionStore(Protocol):
    def consume(self, consumption: PermitConsumption) -> None: ...

    def get(self, permit_id: Identifier) -> PermitConsumption | None: ...


class InMemoryPermitConsumptionStore:
    """Thread-safe replay barrier for the local demonstrator."""

    def __init__(self) -> None:
        self._consumptions: dict[str, PermitConsumption] = {}
        self._lock = RLock()

    def consume(self, consumption: PermitConsumption) -> None:
        with self._lock:
            if consumption.permit_id in self._consumptions:
                raise PermitRejected(
                    PermitRejectionCode.PERMIT_REPLAYED,
                    "permit was already consumed",
                )
            self._consumptions[consumption.permit_id] = consumption

    def get(self, permit_id: Identifier) -> PermitConsumption | None:
        with self._lock:
            return self._consumptions.get(permit_id)
