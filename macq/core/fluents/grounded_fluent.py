from dataclasses import dataclass
from typing import Tuple

from ..planning_object import PlanningObject


@dataclass(frozen=True)
class GroundedFluent:
    """A predicate applied to specific objects."""

    name: str
    objects: Tuple[PlanningObject, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "objects", tuple(self.objects))

    def details(self):
        return f"({' '.join([self.name, *(o.details() for o in self.objects)])})"

    def __str__(self):
        return self.details()

    def __repr__(self):
        return self.details()
