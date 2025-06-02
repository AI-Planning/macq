from typing import Optional


class CircularTypeHierarchyException(Exception):
    def __init__(self, message=None):
        super().__init__()
        self.message = message

    def __str__(self):
        return "Circular Type Hierarchy Error: " + self.message if self.message \
            else "Circular Type Hierarchy Error - validate inputs of ObjectType init function."

def is_circular_type_hierarchy_error(child_type_name: str, parent: "ObjectType"):
    """
    Checks whether adding a `child_type_name` as a child of `parent` creates a circular hierarchy.

    A circular hierarchy occurs when a type becomes its own ancestor or descendant,
    causing inconsistencies in the hierarchical structure. This method ensures the
    validity of the hierarchical relationship by validating the absence of such
    circular dependencies.

    Args:
        child_type_name (ObjectType): The proposed child type in the hierarchical
            relation.
        parent (ObjectType): The parent type to check against for circular
            dependencies.

    Returns:
        bool: True if the addition creates a circular hierarchy, otherwise False.
    """

    current = parent
    while current is not None:
        if current.type_name == child_type_name:
            return True
        current = current.parent
    return False

class ObjectType:
    """clss representation of a type matching the tarski lang sort representation
    the type can be illustrated as a directed graph with no cycles"""
    type_name: str
    parent_type: Optional["ObjectType"]


    def __init__(self, type_name: str ="object", parent=None):
        """if sort has a parent of type DomainSort, input the parent sort name
        if the sort has no learned parent, the parent argument can remain empty"""
        if is_circular_type_hierarchy_error(type_name, parent):
            raise CircularTypeHierarchyException(
                f" Type '{type_name}' would create a circular hierarchy with parent '{parent.type_name}'")

        self.type_name = type_name
        self.parent = parent

    def __eq__(self, other):
        if not isinstance(other, ObjectType):
            return False
        return self.type_name == other.type_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, ObjectType):
            return NotImplemented

        # Check if other is an ancestor of self
        curr = self.parent
        while curr is not None:
            if curr == other:
                return True
            curr = curr.parent
        return False

    def __gt__(self, other):
        if not isinstance(other, ObjectType):
            return NotImplemented

        # Check if self is an ancestor of other
        curr = other.parent
        while curr is not None:
            if curr == self:
                return True
            curr = curr.parent
        return False

    def __str__(self):
        return self.type_name

    def __hash__(self):
        return hash(self.details())


    def details(self):
        postfix = "" if self.parent is None else f" parent: {self.parent}"
        return f"name: {self.type_name}{postfix}"


