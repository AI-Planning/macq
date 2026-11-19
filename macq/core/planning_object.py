from dataclasses import dataclass

from ._value import CachedValue
from .object_type import ObjectType


@dataclass(frozen=True, eq=False)
class PlanningObject(CachedValue):
    """An object of a planning domain, identified by its name and object type."""

    name: str
    obj_type: ObjectType

    def _value_key(self) -> tuple:
        return self.name, self.obj_type

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ is not PlanningObject:
            return NotImplemented
        return self.name == other.name and self.obj_type == other.obj_type

    __hash__ = CachedValue.__hash__

    def details(self):
        return f"{self.obj_type.type_name} {self.name}"

    def __repr__(self):
        return self.details()
