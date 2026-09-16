"""Deterministic Merkle commitments for field and payload evidence."""

from sodif.domain.canonical import sha256_digest
from sodif.domain.types import Digest


def merkle_root(leaves: tuple[Digest, ...]) -> Digest:
    if not leaves:
        raise ValueError("Merkle commitment requires at least one leaf")
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            sha256_digest({"left": level[index], "right": level[index + 1]})
            for index in range(0, len(level), 2)
        ]
    return level[0]
