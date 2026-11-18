from enum import Enum


class DomainModelForm(Enum):
    """The two forms a domain model can take."""

    LIFTED = "lifted"
    GROUNDED = "grounded"


class DomainModelError(ValueError):
    """Raised when a domain model is malformed or can't be converted."""
