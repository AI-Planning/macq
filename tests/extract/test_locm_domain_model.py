import pytest

from macq.core import DomainModelError, DomainModelForm, ObjectType, ParameterBoundFluent
from macq.extract.locm import LOCM, _ActionSchema, _StateFluent


def schema(name, sorts, precond=(), add=(), delete=(), statics=()):
    return _ActionSchema(name, list(sorts), list(precond), list(add), list(delete), list(statics))


def action_named(model, name):
    return next(action for action in model.actions if action.name == name)


def predicate_named(model, name):
    return next(fluent for fluent in model.fluents if fluent.name == name)


def test_builds_a_lifted_domain_model_over_the_learned_sorts():
    state = _StateFluent("sort1_state0", ["sort1"], [0])

    model = LOCM._to_domain_model([schema("open", ["sort1"], precond=[state])])

    assert model.form is DomainModelForm.LIFTED
    assert action_named(model, "open").params[0].object_type == ObjectType("sort1")
    assert action_named(model, "open").positive_preconditions == {ParameterBoundFluent("sort1_state0", [0])}


def test_only_predicates_used_with_several_arities_get_an_arity_suffix():
    one = _StateFluent("sort1_state1", ["sort1"], [0])
    two = _StateFluent("sort1_state1", ["sort1", "sort1"], [0, 1])
    other = _StateFluent("sort1_state2", ["sort1"], [0])

    model = LOCM._to_domain_model(
        [
            schema("pick", ["sort1"], add=[one], delete=[other]),
            schema("stack", ["sort1", "sort1"], precond=[two]),
        ]
    )

    assert {fluent.name for fluent in model.fluents} == {
        "sort1_state1_1",
        "sort1_state1_2",
        "sort1_state2",
    }
    assert action_named(model, "pick").add_effects == {ParameterBoundFluent("sort1_state1_1", [0])}
    assert action_named(model, "stack").positive_preconditions == {
        ParameterBoundFluent("sort1_state1_2", [0, 1])
    }


def test_the_zero_object_binding_is_the_last_parameter():
    zero = _StateFluent("sort0_state0", ["sort0"], [-1])

    model = LOCM._to_domain_model([schema("pick", ["sort1", "sort0"], precond=[zero])])

    assert action_named(model, "pick").positive_preconditions == {ParameterBoundFluent("sort0_state0", [1])}


def test_a_static_precondition_is_one_declared_and_bound_precondition():
    model = LOCM._to_domain_model([schema("put", ["sort1", "sort2"], statics=[("next", 2, 1)])])

    assert action_named(model, "put").positive_preconditions == {ParameterBoundFluent("next", [1, 0])}
    types = [parameter.object_type for parameter in predicate_named(model, "next").parameters]
    assert types == [ObjectType("sort2"), ObjectType("sort1")]


def test_a_static_used_over_different_sorts_is_declared_over_their_common_parent():
    model = LOCM._to_domain_model(
        [
            schema("put", ["sort1"], statics=[("ready", 1)]),
            schema("get", ["sort2"], statics=[("ready", 1)]),
        ]
    )

    assert predicate_named(model, "ready").parameters[0].object_type == ObjectType()


def test_a_static_naming_a_missing_argument_is_rejected():
    with pytest.raises(DomainModelError, match="next"):
        LOCM._to_domain_model([schema("put", ["sort1"], statics=[("next", 2, 1)])])
