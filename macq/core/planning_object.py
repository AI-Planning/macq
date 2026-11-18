from dataclasses import dataclass

from .object_type import ObjectType


@dataclass(frozen=True)
class PlanningObject:
    """An object of a planning domain, identified by its name and object type."""

    name: str
    obj_type: ObjectType

    def details(self):
        return f"{self.obj_type.type_name} {self.name}"

    def __repr__(self):
        return self.details()
