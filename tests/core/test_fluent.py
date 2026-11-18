from dataclasses import FrozenInstanceError

import pytest

from macq.core import (
    GroundedFluent,
    LiftedFluent,
    ObjectType,
    ParameterBoundFluent,
    PlanningObject,
    SignatureParameter,
)

BLOCK = ObjectType("block")
A, B, C, D = (PlanningObject(name, BLOCK) for name in "abcd")


def test_parameters_compare_on_name_and_type():
    assert SignatureParameter("x", BLOCK) == SignatureParameter("x", BLOCK)
    assert hash(SignatureParameter("x", BLOCK)) == hash(SignatureParameter("x", BLOCK))
    assert SignatureParameter("x", BLOCK) != SignatureParameter("x")
    assert SignatureParameter("x", BLOCK) != SignatureParameter("y", BLOCK)


def test_parameter_defaults_to_the_root_type():
    assert SignatureParameter("x").object_type == ObjectType("object")


def test_grounded_fluents_over_different_objects_are_different():
    assert GroundedFluent("on", [A, B]) != GroundedFluent("on", [C, D])
    assert len({GroundedFluent("on", [A, B]), GroundedFluent("on", [C, D])}) == 2


def test_grounded_fluent_argument_order_matters():
    assert GroundedFluent("on", [A, B]) != GroundedFluent("on", [B, A])


def test_identical_grounded_fluents_are_equal():
    assert GroundedFluent("on", [A, B]) == GroundedFluent("on", [A, B])
    assert len({GroundedFluent("on", [A, B]), GroundedFluent("on", [A, B])}) == 1


def test_identical_parameter_bound_fluents_are_equal():
    assert ParameterBoundFluent("on", [0, 1]) == ParameterBoundFluent("on", [0, 1])
    assert len({ParameterBoundFluent("on", [0, 1]), ParameterBoundFluent("on", [0, 1])}) == 1


def test_parameter_bound_fluent_binding_order_matters():
    assert ParameterBoundFluent("on", [0, 1]) != ParameterBoundFluent("on", [1, 0])


def test_lifted_fluents_compare_on_name_and_parameters():
    x, y = SignatureParameter("x", BLOCK), SignatureParameter("y", BLOCK)

    assert LiftedFluent("on", [x, y]) == LiftedFluent("on", [x, y])
    assert hash(LiftedFluent("on", [x, y])) == hash(LiftedFluent("on", [x, y]))
    assert LiftedFluent("on", [x, y]) != LiftedFluent("on", [y, x])
    assert LiftedFluent("on", [x, y]) != LiftedFluent("above", [x, y])


@pytest.mark.parametrize(
    "fluent, attribute",
    [
        (LiftedFluent("on", []), "name"),
        (ParameterBoundFluent("on", []), "name"),
        (GroundedFluent("on", []), "name"),
        (SignatureParameter("x"), "name"),
    ],
)
def test_values_are_immutable(fluent, attribute):
    with pytest.raises(FrozenInstanceError):
        setattr(fluent, attribute, "other")


def test_changing_the_source_list_does_not_change_the_fluent():
    objects = [A, B]
    fluent = GroundedFluent("on", objects)
    objects.append(C)

    assert fluent == GroundedFluent("on", [A, B])
