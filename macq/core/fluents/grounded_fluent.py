from dataclasses import dataclass
from typing import Tuple

from .._value import CachedValue
from ..planning_object import PlanningObject


@dataclass(frozen=True, eq=False)
class GroundedFluent(CachedValue):
    """A predicate applied to specific objects."""

    name: str
    objects: Tuple[PlanningObject, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "objects", tuple(self.objects))

    def _value_key(self) -> tuple:
        return self.name, self.objects

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ is not GroundedFluent:
            return NotImplemented
        return self.name == other.name and self.objects == other.objects

    __hash__ = CachedValue.__hash__

    def details(self):
        return f"({' '.join([self.name, *(o.details() for o in self.objects)])})"

    def __str__(self):
        return self.details()

    def __repr__(self):
        return self.details()
