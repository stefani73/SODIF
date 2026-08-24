"""Explicit domain failures used by pure SODIF services."""


class DomainError(Exception):
    """Base class for expected domain failures."""


class CanonicalizationError(DomainError):
    """Raised when a value cannot be represented deterministically as JSON."""


class InvalidTransition(DomainError):
    """Raised when a workflow attempts a forbidden state transition."""


class InvalidRevisionChain(DomainError):
    """Raised when a revision cannot extend the accepted document history."""
