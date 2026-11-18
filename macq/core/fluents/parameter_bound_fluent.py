from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ParameterBoundFluent:
    """A predicate used inside a lifted action, with each argument given as an index into the action's parameters."""

    name: str
    bounded_params: Tuple[int, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "bounded_params", tuple(self.bounded_params))

    def details(self):
        return f"({' '.join([self.name, *map(str, self.bounded_params)])})"

    def __str__(self):
        return self.details()
