import pytest

from macq.core import (
    GroundedAction,
    GroundedFluent,
    LiftedAction,
    ObjectType,
    ParameterBoundFluent,
    PlanningObject,
    SignatureParameter,
)

BLOCK = ObjectType("block")
TRUCK = ObjectType("truck")
X = SignatureParameter("x", BLOCK)
Y = SignatureParameter("y", BLOCK)
A, B = PlanningObject("a", BLOCK), PlanningObject("b", BLOCK)
ON_01 = ParameterBoundFluent("on", [0, 1])
ON_AB = GroundedFluent("on", [A, B])


def test_new_lifted_action_can_be_hashed():
    assert isinstance(hash(LiftedAction("stack", [X, Y])), int)


def test_negative_preconditions_default_to_an_empty_set():
    assert LiftedAction("stack", [X]).negative_preconditions == set()
    assert GroundedAction("stack", [A]).negative_preconditions == set()


def test_negative_preconditions_cannot_be_set_to_none():
    action = LiftedAction("stack", [X])

    with pytest.raises(TypeError):
        action.negative_preconditions = None


def test_lifted_action_hash_is_stable_when_it_is_updated():
    action = LiftedAction("stack", [X, Y])
    actions = {action}

    action.add_effects.add(ON_01)

    assert action in actions


def test_grounded_action_hash_is_stable_when_it_is_updated():
    action = GroundedAction("stack", [A, B])
    actions = {action}

    action.add_effects.add(ON_AB)

    assert action in actions


def test_lifted_actions_with_different_contents_are_not_equal():
    first = LiftedAction("stack", [X, Y], add_effects={ON_01})
    second = LiftedAction("stack", [X, Y])

    assert first != second
    assert hash(first) == hash(second)


def test_lifted_actions_with_the_same_contents_are_equal():
    first = LiftedAction("stack", [X, Y], positive_preconditions={ON_01})
    second = LiftedAction("stack", [X, Y], positive_preconditions={ON_01})

    assert first == second


def test_lifted_signature_is_the_name_and_parameter_types():
    renamed = [SignatureParameter("p", BLOCK), SignatureParameter("q", BLOCK)]

    assert LiftedAction("stack", [X, Y]).signature == LiftedAction("stack", renamed).signature
    assert (
        LiftedAction("move", [SignatureParameter("x", BLOCK)]).signature
        != LiftedAction("move", [SignatureParameter("x", TRUCK)]).signature
    )


def test_grounded_signature_is_the_name_and_objects():
    assert GroundedAction("stack", [A, B]).signature == GroundedAction("stack", [A, B]).signature
    assert GroundedAction("stack", [A, B]).signature != GroundedAction("stack", [B, A]).signature


def test_grounded_action_keeps_its_cost():
    assert GroundedAction("stack", [A, B], cost=3).cost == 3
    assert GroundedAction("stack", [A, B]).cost is None


def test_grounded_actions_with_different_costs_are_not_equal():
    assert GroundedAction("stack", [A], cost=1) != GroundedAction("stack", [A], cost=2)


def test_grounded_action_has_a_readable_representation():
    assert repr(GroundedAction("stack", [A, B])) == "(stack block a block b)"


def test_lifted_action_has_a_readable_representation():
    assert repr(LiftedAction("stack", [X, Y])) == "(stack x block y block)"


@pytest.mark.parametrize(
    "action, attribute",
    [
        (LiftedAction("stack", [X]), "name"),
        (LiftedAction("stack", [X]), "params"),
        (GroundedAction("stack", [A]), "name"),
        (GroundedAction("stack", [A]), "objects"),
    ],
)
def test_action_signature_cannot_be_changed(action, attribute):
    with pytest.raises(AttributeError):
        setattr(action, attribute, "other")
