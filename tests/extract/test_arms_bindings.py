from types import SimpleNamespace

import pytest

from macq.core import ObjectType, PlanningObject
from macq.core import DomainModelForm, ObjectType, ParameterBoundFluent
from macq.extract.arms import ARMS, _ActionSchema
from macq.trace import Action, Fluent, PartialState

A = PlanningObject("a", ObjectType("block"))
B = PlanningObject("b", ObjectType("block"))
ON_AB = Fluent("on", [A, B])
ON_BA = Fluent("on", [B, A])


def token(state, action=None):
    return SimpleNamespace(state=PartialState(state), action=action)


def schema(name, types, precond=(), add=(), delete=()):
    action = _ActionSchema(name, list(types))
    action.precond, action.add, action.delete = set(precond), set(add), set(delete)
    return action


def bound(name, *indices):
    return ParameterBoundFluent(name, indices)


def only_action(model):
    return next(iter(model.actions))


def test_add_effect_binds_to_the_parameters_seen_in_the_trace():
    stack = Action("stack", [B, A])
    traces = [[token({ON_AB: False}, stack), token({ON_AB: True})]]

    model = ARMS._to_domain_model(
        [schema("stack", ["block", "block"], add=["on block block"])], ARMS._binding_support(traces)
    )

    assert model.form is DomainModelForm.LIFTED
    assert only_action(model).add_effects == {bound("on", 1, 0)}


def test_precondition_and_delete_effect_use_their_own_evidence():
    unstack = Action("unstack", [A, B])
    traces = [[token({ON_AB: True, ON_BA: False}, unstack), token({ON_AB: False, ON_BA: False})]]

    model = ARMS._to_domain_model(
        [schema("unstack", ["block", "block"], precond=["on block block"], delete=["on block block"])],
        ARMS._binding_support(traces),
    )

    action = only_action(model)
    assert action.positive_preconditions == {bound("on", 0, 1)}
    assert action.delete_effects == {bound("on", 0, 1)}


def test_the_binding_with_the_most_support_wins():
    stack = Action("stack", [A, B])
    swapped = Action("stack", [B, A])
    traces = [
        [token({ON_AB: False}, stack), token({ON_AB: True})],
        [token({ON_BA: False}, stack), token({ON_BA: True})],
        [token({ON_AB: False}, swapped), token({ON_AB: True})],
        [token({ON_BA: False}, swapped), token({ON_BA: True})],
        [token({ON_BA: False}, swapped), token({ON_BA: True})],
    ]

    model = ARMS._to_domain_model(
        [schema("stack", ["block", "block"], add=["on block block"])], ARMS._binding_support(traces)
    )

    assert only_action(model).add_effects == {bound("on", 0, 1)}


def test_without_evidence_distinct_parameters_are_preferred_in_order():
    model = ARMS._to_domain_model([schema("stack", ["block", "block"], add=["on block block"])], {})

    assert only_action(model).add_effects == {bound("on", 0, 1)}


def test_a_relation_with_more_arguments_of_a_type_than_parameters_is_dropped_with_a_warning():
    with pytest.warns(UserWarning, match=r"\(on block block\).*precondition.*\(pick block\)"):
        model = ARMS._to_domain_model([schema("pick", ["block"], precond=["on block block"])], {})

    assert only_action(model).positive_preconditions == set()
    assert model.fluents == frozenset()


def test_a_relation_without_arguments_binds_to_nothing():
    model = ARMS._to_domain_model([schema("pick", ["block"], precond=["handempty "])], {})

    assert only_action(model).positive_preconditions == {bound("handempty")}


def test_a_predicate_seen_with_different_types_is_declared_over_their_common_parent():
    model = ARMS._to_domain_model(
        [
            schema("drive", ["truck"], add=["at truck"]),
            schema("carry", ["package"], add=["at package"]),
        ],
        {},
    )

    predicate = next(iter(model.fluents))
    assert predicate.parameters[0].object_type == ObjectType()


@pytest.mark.parametrize(
    "part, label", [("precond", "precondition"), ("add", "add effect"), ("delete", "delete effect")]
)
def test_a_relation_no_parameter_can_fill_is_dropped_with_a_warning(part, label):
    action = schema("load", ["package"], **{part: ["at truck"]})

    with pytest.warns(UserWarning, match=rf"\(at truck\).*{label}.*\(load package\)"):
        model = ARMS._to_domain_model([action], {})

    assert only_action(model).add_effects == set()
    assert model.fluents == frozenset()


def test_relations_that_fit_are_kept_when_another_is_dropped():
    action = schema("load", ["package"], add=["at truck", "held package"])

    with pytest.warns(UserWarning):
        model = ARMS._to_domain_model([action], {})

    assert only_action(model).add_effects == {bound("held", 0)}


def test_no_warning_when_every_relation_fits(recwarn):
    ARMS._to_domain_model([schema("load", ["package"], add=["held package"])], {})

    assert len(recwarn) == 0
