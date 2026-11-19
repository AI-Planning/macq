"""Builds `macq.core` objects and object types from domains and problems parsed by the `pddl` library."""

from typing import Dict, Iterable

from pddl.core import Domain

from ..core import ObjectType, PlanningObject
from ..core.object_type import ROOT_TYPE_NAME


def object_types(domain: Domain) -> Dict[str, ObjectType]:
    """Returns each of the domain's object types by name, with its parent chain, including `object`."""
    parents = {str(name): None if parent is None else str(parent) for name, parent in domain.types.items()}
    types: Dict[str, ObjectType] = {ROOT_TYPE_NAME: ObjectType()}

    def build(name: str, descendants: tuple) -> ObjectType:
        if name in types:
            return types[name]
        if name in descendants:
            raise ValueError(f"The domain's object types form a cycle through {name!r}.")
        parent = parents.get(name)
        types[name] = ObjectType(name, None if parent is None else build(parent, descendants + (name,)))
        return types[name]

    for name in parents:
        build(name, ())
    return types


def planning_objects(domain: Domain, objects: Iterable) -> Dict[str, PlanningObject]:
    """Returns each `pddl` object (a constant or a problem object) as a `core` object, by name."""
    types = object_types(domain)
    result = {}
    for obj in objects:
        type_name = str(obj.type_tag or ROOT_TYPE_NAME)
        if type_name not in types:
            raise ValueError(f"Object {obj.name} has the undeclared object type {type_name!r}.")
        result[str(obj.name)] = PlanningObject(str(obj.name), types[type_name])
    return result
