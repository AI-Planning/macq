from dataclasses import dataclass
from typing import Optional

from ._value import CachedValue

ROOT_TYPE_NAME = "object"


class CircularTypeHierarchyException(Exception):
    def __init__(self, message=None):
        super().__init__()
        self.message = message

    def __str__(self):
        return "Circular Type Hierarchy Error: " + self.message if self.message \
            else "Circular Type Hierarchy Error - validate inputs of ObjectType init function."


def is_circular_type_hierarchy_error(child_type_name: str, parent: Optional["ObjectType"]) -> bool:
    """Returns whether making `child_type_name` a child of `parent` would make a type its own ancestor."""
    current = parent
    while current is not None:
        if current.type_name == child_type_name:
            return True
        current = current.parent
    return False


@dataclass(frozen=True, eq=False)
class ObjectType(CachedValue):
    """A named category of planning objects.

    `object` is the implicit root of every hierarchy, so a type created without a parent is a direct
    child of `object`. Types compare on their name and their parent.
    """

    type_name: str = ROOT_TYPE_NAME
    parent: Optional["ObjectType"] = None

    def __post_init__(self):
        if is_circular_type_hierarchy_error(self.type_name, self.parent):
            raise CircularTypeHierarchyException(
                f"Type '{self.type_name}' would create a circular hierarchy with parent '{self.parent.type_name}'"
            )
        if self.parent is None and self.type_name != ROOT_TYPE_NAME:
            object.__setattr__(self, "parent", ObjectType())

    def _value_key(self) -> tuple:
        return self.type_name, self.parent

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ is not ObjectType:
            return NotImplemented
        return self.type_name == other.type_name and self.parent == other.parent

    __hash__ = CachedValue.__hash__

    def is_subtype_of(self, other: "ObjectType") -> bool:
        """Returns whether this type is `other` or one of its descendants."""
        return self == other or self < other

    def __lt__(self, other):
        if not isinstance(other, ObjectType):
            return NotImplemented
        current = self.parent
        while current is not None:
            if current == other:
                return True
            current = current.parent
        return False

    def __gt__(self, other):
        if not isinstance(other, ObjectType):
            return NotImplemented
        return other < self

    def __str__(self):
        return self.type_name

    def details(self):
        postfix = "" if self.parent is None else f" parent: {self.parent}"
        return f"name: {self.type_name}{postfix}"
