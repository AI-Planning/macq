from dataclasses import dataclass
from typing import Tuple

from ..signature_parameter import SignatureParameter


@dataclass(frozen=True)
class LiftedFluent:
    """A predicate declaration: a name and its typed parameters."""

    name: str
    parameters: Tuple[SignatureParameter, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "parameters", tuple(self.parameters))

    def details(self):
        return f"({' '.join([self.name, *(p.details() for p in self.parameters)])})"

    def __str__(self):
        return self.details()
