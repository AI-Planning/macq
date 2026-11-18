"""Converts what extraction techniques learn into `macq.core` domain model parts."""

from typing import Union

from ..core import DomainModelError, GroundedFluent, ObjectType, PlanningObject
from ..trace import Fluent
from ..trace import PlanningObject as TracePlanningObject


def to_planning_object(obj: Union[TracePlanningObject, str]) -> PlanningObject:
    """Returns the `core` object for a trace object or its "type name" text."""
    if not isinstance(obj, str):
        return PlanningObject(obj.name, ObjectType(obj.obj_type))
    parts = obj.split(" ")
    if len(parts) != 2:
        raise DomainModelError(f"Expected an object as 'type name', got {obj!r}.")
    return PlanningObject(parts[1], ObjectType(parts[0]))


def to_grounded_fluent(fluent: Union[Fluent, str]) -> GroundedFluent:
    """Returns the `core` fluent for a trace fluent or its "(name type object ...)" text."""
    if not isinstance(fluent, str):
        return GroundedFluent(fluent.name, tuple(map(to_planning_object, fluent.objects)))
    if not (fluent.startswith("(") and fluent.endswith(")")):
        raise DomainModelError(f"Expected a fluent as '(name type object ...)', got {fluent!r}.")
    name, *tokens = fluent[1:-1].split(" ")
    if not name or len(tokens) % 2:
        raise DomainModelError(f"Expected a fluent as '(name type object ...)', got {fluent!r}.")
    pairs = zip(tokens[::2], tokens[1::2])
    return GroundedFluent(name, tuple(PlanningObject(obj, ObjectType(kind)) for kind, obj in pairs))
