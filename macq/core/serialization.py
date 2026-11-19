"""Converts domain models to and from macq's versioned JSON document format."""

import json
from typing import Dict, List

from .actions import GroundedAction, LiftedAction
from .domain_model_form import DomainModelError, DomainModelForm
from .fluents import GroundedFluent, LiftedFluent, ParameterBoundFluent
from .object_type import ROOT_TYPE_NAME, ObjectType
from .planning_object import PlanningObject
from .signature_parameter import SignatureParameter

FORMAT_VERSION = 1

_FLUENT_SETS = ("positive_preconditions", "negative_preconditions", "add_effects", "delete_effects")


def domain_model_to_json(model) -> str:
    """Returns the JSON text of `model`. The same domain model always produces the same text."""
    document = {
        "format_version": FORMAT_VERSION,
        "form": model.form.value,
        "object_types": sorted(
            ({"name": t.type_name, "parent": t.parent.type_name} for t in model.object_types),
            key=lambda entry: entry["name"],
        ),
    }
    if model.form is DomainModelForm.LIFTED:
        document["fluents"] = _sorted_entries(map(_write_predicate, model.fluents))
        document["actions"] = _sorted_entries(map(_write_lifted_action, model.actions))
    else:
        objects = {obj for fluent in model.fluents for obj in fluent.objects}
        objects |= {obj for action in model.actions for obj in action.objects}
        document["objects"] = sorted(
            ({"name": obj.name, "type": obj.obj_type.type_name} for obj in objects),
            key=lambda entry: entry["name"],
        )
        document["fluents"] = _sorted_entries(map(_write_grounded_fluent, model.fluents))
        document["actions"] = _sorted_entries(map(_write_grounded_action, model.actions))
    return json.dumps(document, indent=2, sort_keys=True)


def domain_model_parts_from_json(text: str) -> dict:
    """Returns the constructor arguments of the domain model described by `text`."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise DomainModelError(f"Domain model document is not valid JSON: {error}.") from error
    if not isinstance(document, dict):
        raise DomainModelError("Domain model document must be a JSON object.")
    version = document.get("format_version")
    if version != FORMAT_VERSION:
        raise DomainModelError(f"Unsupported domain model format version: {version!r}.")

    try:
        return _read_parts(document)
    except KeyError as error:
        raise DomainModelError(f"Domain model document is missing {error}.") from error
    except (TypeError, AttributeError) as error:
        raise DomainModelError(f"Domain model document is malformed: {error}.") from error


def _sorted_entries(entries) -> List[dict]:
    return sorted(entries, key=lambda entry: (entry["name"], json.dumps(entry, sort_keys=True)))


def _write_parameter(parameter: SignatureParameter) -> dict:
    return {"name": parameter.name, "type": parameter.object_type.type_name}


def _write_predicate(fluent: LiftedFluent) -> dict:
    return {"name": fluent.name, "parameters": [_write_parameter(p) for p in fluent.parameters]}


def _write_bound_fluent(fluent: ParameterBoundFluent) -> dict:
    return {"name": fluent.name, "arguments": list(fluent.bounded_params)}


def _write_grounded_fluent(fluent: GroundedFluent) -> dict:
    return {"name": fluent.name, "arguments": [obj.name for obj in fluent.objects]}


def _write_fluent_sets(action, write_fluent) -> dict:
    return {
        field: _sorted_entries(map(write_fluent, getattr(action, field))) for field in _FLUENT_SETS
    }


def _write_lifted_action(action: LiftedAction) -> dict:
    return {
        "name": action.name,
        "parameters": [_write_parameter(p) for p in action.params],
        **_write_fluent_sets(action, _write_bound_fluent),
    }


def _write_grounded_action(action: GroundedAction) -> dict:
    return {
        "name": action.name,
        "arguments": [obj.name for obj in action.objects],
        "cost": action.cost,
        **_write_fluent_sets(action, _write_grounded_fluent),
    }


def _read_parts(document: dict) -> dict:
    try:
        form = DomainModelForm(document["form"])
    except ValueError as error:
        raise DomainModelError(f"Unknown domain model form: {document['form']!r}.") from error

    object_types = _read_object_types(document["object_types"])
    if form is DomainModelForm.LIFTED:
        fluents = [_read_predicate(entry, object_types) for entry in document["fluents"]]
        actions = [_read_lifted_action(entry, object_types) for entry in document["actions"]]
    else:
        objects = _read_objects(document["objects"], object_types)
        fluents = [_read_grounded_fluent(entry, objects) for entry in document["fluents"]]
        actions = [_read_grounded_action(entry, objects) for entry in document["actions"]]
    return {
        "form": form,
        "fluents": fluents,
        "actions": actions,
        "object_types": [t for t in object_types.values() if t.parent is not None],
    }


def _read_object_types(entries: List[dict]) -> Dict[str, ObjectType]:
    parents: Dict[str, str] = {}
    for entry in entries:
        name = entry["name"]
        if name in parents or name == ROOT_TYPE_NAME:
            raise DomainModelError(f"Object type '{name}' is listed more than once.")
        parents[name] = entry["parent"]

    resolved = {ROOT_TYPE_NAME: ObjectType()}

    def resolve(name: str, descendants: tuple) -> ObjectType:
        if name in resolved:
            return resolved[name]
        if name in descendants:
            raise DomainModelError(f"Cycle in object types at '{name}'.")
        if name not in parents:
            raise DomainModelError(f"Unknown object type '{name}'.")
        resolved[name] = ObjectType(name, resolve(parents[name], (*descendants, name)))
        return resolved[name]

    for name in parents:
        resolve(name, ())
    return resolved


def _lookup(table: dict, name: str, kind: str):
    if name not in table:
        raise DomainModelError(f"Unknown {kind} '{name}'.")
    return table[name]


def _read_parameters(entries: List[dict], object_types: Dict[str, ObjectType]) -> List[SignatureParameter]:
    return [
        SignatureParameter(entry["name"], _lookup(object_types, entry["type"], "object type"))
        for entry in entries
    ]


def _read_predicate(entry: dict, object_types: Dict[str, ObjectType]) -> LiftedFluent:
    return LiftedFluent(entry["name"], _read_parameters(entry["parameters"], object_types))


def _read_fluent_sets(entry: dict, read_fluent) -> dict:
    return {field: [read_fluent(fluent) for fluent in entry[field]] for field in _FLUENT_SETS}


def _read_lifted_action(entry: dict, object_types: Dict[str, ObjectType]) -> LiftedAction:
    return LiftedAction(
        entry["name"],
        _read_parameters(entry["parameters"], object_types),
        **_read_fluent_sets(entry, lambda f: ParameterBoundFluent(f["name"], f["arguments"])),
    )


def _read_objects(entries: List[dict], object_types: Dict[str, ObjectType]) -> Dict[str, PlanningObject]:
    objects: Dict[str, PlanningObject] = {}
    for entry in entries:
        name = entry["name"]
        if name in objects:
            raise DomainModelError(f"Object '{name}' is listed more than once.")
        objects[name] = PlanningObject(name, _lookup(object_types, entry["type"], "object type"))
    return objects


def _read_grounded_fluent(entry: dict, objects: Dict[str, PlanningObject]) -> GroundedFluent:
    return GroundedFluent(entry["name"], [_lookup(objects, name, "object") for name in entry["arguments"]])


def _read_grounded_action(entry: dict, objects: Dict[str, PlanningObject]) -> GroundedAction:
    return GroundedAction(
        entry["name"],
        [_lookup(objects, name, "object") for name in entry["arguments"]],
        cost=entry["cost"],
        **_read_fluent_sets(entry, lambda fluent: _read_grounded_fluent(fluent, objects)),
    )
