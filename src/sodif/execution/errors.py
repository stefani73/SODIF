"""Failures at the controlled API execution boundary."""


class ExecutionRejected(ValueError):
    """Raised when authorization and the presented action differ."""
