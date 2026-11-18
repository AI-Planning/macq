from collections import Counter, defaultdict
from typing import Dict, FrozenSet, Iterable, List, Optional, Set

from .actions import GroundedAction, LiftedAction
from .domain_model_form import DomainModelError, DomainModelForm
from .fluents import GroundedFluent, LiftedFluent, ParameterBoundFluent
from .object_type import ROOT_TYPE_NAME, ObjectType
from .pddl_writer import domain_to_pddl
from .planning_object import PlanningObject
from .serialization import domain_model_parts_from_json, domain_model_to_json
from .signature_parameter import SignatureParameter

_PART_KINDS = {
    DomainModelForm.LIFTED: (LiftedFluent, LiftedAction, ParameterBoundFluent),
    DomainModelForm.GROUNDED: (GroundedFluent, GroundedAction, GroundedFluent),
}


class DomainModel:
    """The actions and predicates of a domain, in lifted or grounded form.

    A domain model is checked for well-formedness when it is constructed, and again before it is
    written out, because its actions can be updated in between. Learned content that is well-formed but
    contradictory is accepted.
    """

    def __init__(
        self,
        form: DomainModelForm,
        fluents: Iterable,
        actions: Iterable,
        object_types: Iterable[ObjectType] = (),
    ):
        if not isinstance(form, DomainModelForm):
            raise DomainModelError(f"A domain model's form must be a DomainModelForm, got {form!r}.")
        fluents, actions = list(fluents), list(actions)

        self.form = form
        self.fluents: FrozenSet = frozenset(fluents)
        self.actions: FrozenSet = frozenset(actions)
        self._check_part_kinds()
        self._reject_shared_signatures(actions)
        self.object_types: FrozenSet[ObjectType] = self._collect_object_types(object_types)
        self.validate()

    def validate(self) -> None:
        """Raises a DomainModelError if this domain model is malformed."""
        self._check_part_kinds()
        self._check_object_types()
        _reject_case_clashes("Action", {action.name for action in self.actions})
        if self.form is DomainModelForm.LIFTED:
            self._check_lifted_parts()
        else:
            self._check_grounded_parts()

    def details(self) -> str:
        """Returns a readable summary of this domain model's fluents and actions, in sorted order."""
        fluents = ", ".join(sorted(map(str, self.fluents)))
        lines = ["Domain model:", f"  Fluents: {fluents}", "  Actions:"]
        for action in sorted(self.actions, key=str):
            lines.append(f"    {action}:")
            lines += _section("precond", action.positive_preconditions)
            if action.negative_preconditions:
                lines += _section("negative precond", action.negative_preconditions)
            lines += _section("add", action.add_effects)
            lines += _section("delete", action.delete_effects)
        return "\n".join(lines) + "\n"

    def to_pddl(self, domain_name: str, filepath: Optional[str] = None) -> str:
        """Returns this domain model as PDDL domain text.

        Args:
            domain_name (str):
                The name of the domain.
            filepath (str):
                Optional; If supplied, the text is also written to this file.

        Raises:
            DomainModelError: If this domain model is malformed, has overloaded actions, or is grounded
                and has different fluents or actions that flatten to the same PDDL symbol.
        """
        self.validate()
        text = domain_to_pddl(self, domain_name)
        if filepath is not None:
            with open(filepath, "w") as fp:
                fp.write(text)
        return text

    def serialize(self, filepath: Optional[str] = None) -> str:
        """Returns this domain model as versioned JSON text that `deserialize` reads back losslessly.

        Args:
            filepath (str):
                Optional; If supplied, the text is also written to this file.

        Raises:
            DomainModelError: If this domain model is malformed.
        """
        self.validate()
        text = domain_model_to_json(self)
        if filepath is not None:
            with open(filepath, "w") as fp:
                fp.write(text)
        return text

    @classmethod
    def deserialize(cls, text: str) -> "DomainModel":
        """Returns the domain model described by JSON text from `serialize`.

        Raises:
            DomainModelError: If the text is malformed, has an unsupported format version, or describes
                a malformed domain model.
        """
        return cls(**domain_model_parts_from_json(text))

    def __eq__(self, other):
        return (
            isinstance(other, DomainModel)
            and self.form is other.form
            and self.fluents == other.fluents
            and self.actions == other.actions
            and self.object_types == other.object_types
        )

    __hash__ = None

    def _check_part_kinds(self) -> None:
        fluent_kind, action_kind, action_fluent_kind = _PART_KINDS[self.form]
        for fluent in self.fluents:
            self._require_kind(fluent, fluent_kind)
        for action in self.actions:
            self._require_kind(action, action_kind)
            for fluent in _fluents_used_by(action):
                self._require_kind(fluent, action_fluent_kind)

    def _require_kind(self, part, kind: type) -> None:
        if not isinstance(part, kind):
            raise DomainModelError(f"A {self.form.value} domain model can't contain {part!r} here.")

    @staticmethod
    def _reject_shared_signatures(actions: List) -> None:
        counts = Counter(action.signature for action in actions)
        for action in actions:
            if counts[action.signature] > 1:
                raise DomainModelError(f"More than one action has the signature of {action!r}.")

    def _collect_object_types(self, declared: Iterable[ObjectType]) -> FrozenSet[ObjectType]:
        collected: Set[ObjectType] = set()
        for object_type in [*declared, *self._used_object_types()]:
            current = object_type
            while current.parent is not None:
                collected.add(current)
                current = current.parent
        return frozenset(collected)

    def _used_object_types(self) -> List[ObjectType]:
        if self.form is DomainModelForm.LIFTED:
            parameters = [p for fluent in self.fluents for p in fluent.parameters]
            parameters += [p for action in self.actions for p in action.params]
            return [parameter.object_type for parameter in parameters]
        return [obj.obj_type for obj in self._objects()]

    def _objects(self) -> Set[PlanningObject]:
        objects = {obj for fluent in self.fluents for obj in fluent.objects}
        return objects | {obj for action in self.actions for obj in action.objects}

    def _check_object_types(self) -> None:
        parents: Dict[str, Set] = defaultdict(set)
        for object_type in self.object_types:
            parents[object_type.type_name].add(object_type.parent)
        for name, found in parents.items():
            if len(found) > 1:
                raise DomainModelError(f"Object type '{name}' has more than one parent.")
        _reject_case_clashes("Object type", {*parents, ROOT_TYPE_NAME})

    def _check_lifted_parts(self) -> None:
        counts = Counter(fluent.name for fluent in self.fluents)
        for name, count in counts.items():
            if count > 1:
                raise DomainModelError(f"Predicate '{name}' is declared more than once.")
        _reject_case_clashes("Predicate", set(counts))

        predicates = {fluent.name: fluent for fluent in self.fluents}
        for predicate in self.fluents:
            _require_distinct_parameter_names(predicate.name, predicate.parameters)
        for action in self.actions:
            _require_distinct_parameter_names(action.name, action.params)
            for fluent in _fluents_used_by(action):
                _check_bound_fluent(action, fluent, predicates)

    def _check_grounded_parts(self) -> None:
        _reject_case_clashes("Fluent", {fluent.name for fluent in self.fluents})

        object_types: Dict[str, Set[ObjectType]] = defaultdict(set)
        for obj in self._objects():
            object_types[obj.name].add(obj.obj_type)
        for name, found in object_types.items():
            if len(found) > 1:
                raise DomainModelError(f"Object '{name}' has more than one object type.")
        _reject_case_clashes("Object", set(object_types))

        for action in self.actions:
            for fluent in _fluents_used_by(action):
                if fluent not in self.fluents:
                    raise DomainModelError(f"Action {action!r} uses undeclared fluent {fluent}.")


def _section(title: str, fluents: Iterable) -> List[str]:
    return [f"      {title}:", *(f"        {fluent}" for fluent in sorted(map(str, fluents)))]


def _fluents_used_by(action) -> Set:
    return (
        action.positive_preconditions
        | action.negative_preconditions
        | action.add_effects
        | action.delete_effects
    )


def _reject_case_clashes(kind: str, names: Set[str]) -> None:
    spellings: Dict[str, List[str]] = defaultdict(list)
    for name in names:
        spellings[name.casefold()].append(name)
    for found in spellings.values():
        if len(found) > 1:
            raise DomainModelError(f"{kind} names differ only by case: {sorted(found)}.")


def _require_distinct_parameter_names(owner: str, parameters: Iterable[SignatureParameter]) -> None:
    counts = Counter(parameter.name.casefold() for parameter in parameters)
    repeated = sorted(name for name, count in counts.items() if count > 1)
    if repeated:
        raise DomainModelError(f"'{owner}' repeats the parameter names {repeated}.")


def _check_bound_fluent(
    action: LiftedAction, fluent: ParameterBoundFluent, predicates: Dict[str, LiftedFluent]
) -> None:
    predicate = predicates.get(fluent.name)
    if predicate is None:
        raise DomainModelError(f"Action {action!r} uses undeclared predicate '{fluent.name}'.")
    if len(fluent.bounded_params) != len(predicate.parameters):
        raise DomainModelError(
            f"Action {action!r} gives predicate '{fluent.name}' {len(fluent.bounded_params)} arguments, "
            f"but it takes {len(predicate.parameters)}."
        )
    for index, declared in zip(fluent.bounded_params, predicate.parameters):
        if not 0 <= index < len(action.params):
            raise DomainModelError(
                f"Action {action!r} binds predicate '{fluent.name}' to parameter index {index}, "
                "which is out of range."
            )
        argument_type = action.params[index].object_type
        if not argument_type.is_subtype_of(declared.object_type):
            raise DomainModelError(
                f"Action {action!r} passes type '{argument_type}' to predicate '{fluent.name}', "
                f"which expects '{declared.object_type}'."
            )
