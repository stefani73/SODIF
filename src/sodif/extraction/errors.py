"""Errors raised by external document interpreters."""


class DocumentExtractionError(ValueError):
    pass


class ExtractionDependencyError(DocumentExtractionError):
    pass
