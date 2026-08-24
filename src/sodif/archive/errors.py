"""Explicit failures raised by the document archive boundary."""


class ArchiveError(RuntimeError):
    """Base class for archive failures that must stop document processing."""


class ArchiveConflict(ArchiveError):
    """The requested revision conflicts with an existing archive record."""


class ArchiveNotFound(ArchiveError):
    """The requested archive record does not exist."""


class ArchiveIntegrityError(ArchiveError):
    """Stored or supplied bytes do not match their declared digest."""
