"""Expected failures at the semantic-verification boundary."""


class VerificationInputError(ValueError):
    """Raised when independent semantic evidence is structurally inconsistent."""


class SemanticNormalizationError(ValueError):
    """Raised when a field cannot be normalized under its declared semantic type."""
