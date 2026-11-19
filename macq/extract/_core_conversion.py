"""Converts what extraction techniques learn into `macq.core` domain model parts."""

from typing import Iterable, List, Sequence, Union

from ..core import DomainModelError, GroundedFluent, ObjectType, PlanningObject, SignatureParameter
from ..core.object_type import ROOT_TYPE_NAME
from ..trace import Fluent


def to_parameters(type_names: Iterable[str]) -> List[SignatureParameter]:
    """Returns parameters named `x0`, `x1`, ... with the given object types."""
    return [SignatureParameter(f"x{i}", ObjectType(name)) for i, name in enumerate(type_names)]


def common_types(signatures: Iterable[Sequence[str]]) -> List[str]:
    """Returns each argument's type, using `object` where the given signatures disagree."""
    return [types[0] if len(set(types)) == 1 else ROOT_TYPE_NAME for types in zip(*signatures)]


def to_planning_object(obj: Union[PlanningObject, str]) -> PlanningObject:
    """Returns the object a learned model uses for a trace object or its "type name" text.

    Learned models keep flat object types, so a trace object's type keeps its name but not its parents.
    """
    if not isinstance(obj, str):
        return PlanningObject(obj.name, ObjectType(obj.obj_type.type_name))
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
