"""Writes a domain model as PDDL domain text."""

from collections import Counter
from typing import Callable, Iterable, List

from .domain_model_form import DomainModelError, DomainModelForm
from .fluents import GroundedFluent, ParameterBoundFluent
from .object_type import ROOT_TYPE_NAME, ObjectType
from .signature_parameter import SignatureParameter


def domain_to_pddl(model, domain_name: str) -> str:
    """Returns the PDDL domain text of `model`, with every section in a stable order."""
    if model.form is DomainModelForm.LIFTED:
        predicates, actions = _lifted_sections(model)
    else:
        predicates, actions = _grounded_sections(model)

    lines = [f"(define (domain {domain_name})", f"  (:requirements {' '.join(_requirements(model))})"]
    if model.form is DomainModelForm.LIFTED and model.object_types:
        lines += _section(":types", map(_type_line, sorted(model.object_types, key=_type_order)))
    if predicates:
        lines += _section(":predicates", predicates)
    return "\n".join([*lines, *actions, ")"]) + "\n"


def _requirements(model) -> List[str]:
    requirements = [":strips"]
    if model.form is DomainModelForm.LIFTED and model.object_types:
        requirements.append(":typing")
    if any(action.negative_preconditions for action in model.actions):
        requirements.append(":negative-preconditions")
    return requirements


def _section(keyword: str, lines: Iterable[str]) -> List[str]:
    return [f"  ({keyword}", *(f"    {line}" for line in lines), "  )"]


def _type_order(object_type: ObjectType):
    depth = 0
    current = object_type
    while current.parent is not None:
        depth += 1
        current = current.parent
    return depth, object_type.type_name


def _type_line(object_type: ObjectType) -> str:
    return f"{object_type.type_name} - {object_type.parent.type_name}"


def _lifted_sections(model):
    overloaded = sorted(
        name for name, count in Counter(action.name for action in model.actions).items() if count > 1
    )
    if overloaded:
        raise DomainModelError(f"PDDL can't express overloaded actions: {overloaded}.")

    typed = bool(model.object_types)

    def parameter(param: SignatureParameter) -> str:
        # The pddl library rejects `?x - object`, so the root type is left unwritten. PDDL then gives
        # the parameter the type of the next typed parameter, if there is one.
        if typed and param.object_type.type_name != ROOT_TYPE_NAME:
            return f"?{param.name} - {param.object_type}"
        return f"?{param.name}"

    def parameters(params: Iterable[SignatureParameter]) -> str:
        return " ".join(map(parameter, params))

    predicates = [
        f"({' '.join(filter(None, [fluent.name, parameters(fluent.parameters)]))})"
        for fluent in sorted(model.fluents, key=lambda fluent: fluent.name)
    ]
    actions = []
    for action in sorted(model.actions, key=lambda action: action.name):
        def atom(fluent: ParameterBoundFluent) -> str:
            arguments = (f"?{action.params[index].name}" for index in fluent.bounded_params)
            return f"({' '.join([fluent.name, *arguments])})"

        actions += _action_lines(action.name, parameters(action.params), action, atom)
    return predicates, actions


def _grounded_sections(model):
    fluent_symbols = {fluent: _flatten(fluent.name, fluent.objects) for fluent in model.fluents}
    action_symbols = {action: _flatten(action.name, action.objects) for action in model.actions}
    _reject_shared_symbols("fluents", fluent_symbols.values())
    _reject_shared_symbols("actions", action_symbols.values())

    def atom(fluent: GroundedFluent) -> str:
        return f"({fluent_symbols[fluent]})"

    actions = []
    for action in sorted(model.actions, key=action_symbols.get):
        actions += _action_lines(action_symbols[action], "", action, atom)
    return sorted(f"({symbol})" for symbol in fluent_symbols.values()), actions


def _flatten(name: str, objects) -> str:
    return "_".join([name, *(obj.name for obj in objects)])


def _reject_shared_symbols(kind: str, symbols: Iterable[str]) -> None:
    symbols = list(symbols)
    counts = Counter(symbol.casefold() for symbol in symbols)
    shared = sorted({symbol for symbol in symbols if counts[symbol.casefold()] > 1})
    if shared:
        raise DomainModelError(f"Different grounded {kind} flatten to the same PDDL symbol: {shared}.")


def _action_lines(name: str, parameters: str, action, atom: Callable) -> List[str]:
    return [
        f"  (:action {name}",
        f"    :parameters ({parameters})",
        f"    :precondition {_conjunction(action.positive_preconditions, action.negative_preconditions, atom)}",
        f"    :effect {_conjunction(action.add_effects, action.delete_effects, atom)}",
        "  )",
    ]


def _conjunction(positive: Iterable, negative: Iterable, atom: Callable) -> str:
    literals = sorted(map(atom, positive)) + [f"(not {text})" for text in sorted(map(atom, negative))]
    return f"(and {' '.join(literals)})" if literals else "(and)"
