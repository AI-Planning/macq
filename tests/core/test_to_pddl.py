import pytest
from pddl import parse_domain

from macq.core import (
    DomainModel,
    DomainModelError,
    DomainModelForm,
    GroundedAction,
    GroundedFluent,
    LiftedAction,
    LiftedFluent,
    ObjectType,
    ParameterBoundFluent,
    PlanningObject,
    SignatureParameter,
)

LIFTED = DomainModelForm.LIFTED
GROUNDED = DomainModelForm.GROUNDED

BLOCK = ObjectType("block")
SMALL = ObjectType("small", BLOCK)
X = SignatureParameter("x", BLOCK)
Y = SignatureParameter("y", BLOCK)
ON = LiftedFluent("on", [X, Y])
CLEAR = LiftedFluent("clear", [X])

A, B = PlanningObject("a", BLOCK), PlanningObject("b", BLOCK)
ON_AB = GroundedFluent("on", [A, B])
CLEAR_B = GroundedFluent("clear", [B])


def normalized(text):
    return " ".join(text.split())


def stack():
    return LiftedAction(
        "stack",
        [X, Y],
        positive_preconditions={ParameterBoundFluent("clear", [1])},
        negative_preconditions={ParameterBoundFluent("on", [1, 0])},
        add_effects={ParameterBoundFluent("on", [0, 1])},
        delete_effects={ParameterBoundFluent("clear", [1])},
    )


def grounded_stack(**kwargs):
    return GroundedAction(
        "stack",
        [A, B],
        positive_preconditions={CLEAR_B},
        negative_preconditions={ON_AB},
        add_effects={ON_AB},
        delete_effects={CLEAR_B},
        **kwargs,
    )


def test_lifted_domain_is_exported_with_its_parameter_bindings():
    model = DomainModel(LIFTED, {ON, CLEAR}, {stack()}, object_types=[SMALL])

    assert normalized(model.to_pddl("blocks")) == normalized(
        """
        (define (domain blocks)
          (:requirements :strips :typing :negative-preconditions)
          (:types
            block - object
            small - block
          )
          (:predicates
            (clear ?x - block)
            (on ?x - block ?y - block)
          )
          (:action stack
            :parameters (?x - block ?y - block)
            :precondition (and (clear ?y) (not (on ?y ?x)))
            :effect (and (on ?x ?y) (not (clear ?y)))
          )
        )
        """
    )


def test_grounded_domain_is_exported_as_parameterless_actions():
    model = DomainModel(GROUNDED, {ON_AB, CLEAR_B}, {grounded_stack()})

    assert normalized(model.to_pddl("blocks")) == normalized(
        """
        (define (domain blocks)
          (:requirements :strips :negative-preconditions)
          (:predicates
            (clear_b)
            (on_a_b)
          )
          (:action stack_a_b
            :parameters ()
            :precondition (and (clear_b) (not (on_a_b)))
            :effect (and (on_a_b) (not (clear_b)))
          )
        )
        """
    )


def test_negative_preconditions_requirement_is_only_declared_when_needed():
    action = LiftedAction("drop", [X], delete_effects={ParameterBoundFluent("clear", [0])})

    text = DomainModel(LIFTED, {CLEAR}, {action}).to_pddl("blocks")

    assert ":negative-preconditions" not in text


def test_untyped_domain_does_not_declare_types():
    param = SignatureParameter("x")
    predicate = LiftedFluent("held", [param])
    action = LiftedAction("grab", [param], add_effects={ParameterBoundFluent("held", [0])})

    assert normalized(DomainModel(LIFTED, {predicate}, {action}).to_pddl("d")) == normalized(
        """
        (define (domain d)
          (:requirements :strips)
          (:predicates
            (held ?x)
          )
          (:action grab
            :parameters (?x)
            :precondition (and)
            :effect (and (held ?x))
          )
        )
        """
    )


def test_child_types_are_listed_after_their_parents():
    aaa = ObjectType("aaa", ObjectType("zzz"))

    text = normalized(DomainModel(LIFTED, set(), set(), object_types=[aaa]).to_pddl("d"))

    assert "(:types zzz - object aaa - zzz )" in text


def test_names_keep_their_case():
    param = SignatureParameter("Item", ObjectType("Block"))
    predicate = LiftedFluent("onTable", [param])
    action = LiftedAction("PickUp", [param], delete_effects={ParameterBoundFluent("onTable", [0])})

    text = DomainModel(LIFTED, {predicate}, {action}).to_pddl("MyDomain")

    for expected in ["(domain MyDomain)", "Block - object", "(onTable ?Item - Block)", "(:action PickUp"]:
        assert expected in text


def test_output_does_not_depend_on_input_order():
    other = LiftedAction("unstack", [X, Y], add_effects={ParameterBoundFluent("clear", [1])})

    first = DomainModel(LIFTED, [ON, CLEAR], [stack(), other]).to_pddl("blocks")
    second = DomainModel(LIFTED, [CLEAR, ON], [other, stack()]).to_pddl("blocks")

    assert first == second


def test_cost_is_not_exported():
    model = DomainModel(GROUNDED, {ON_AB, CLEAR_B}, {grounded_stack(cost=3)})

    assert model.to_pddl("blocks") == DomainModel(GROUNDED, {ON_AB, CLEAR_B}, {grounded_stack()}).to_pddl("blocks")


def test_domain_is_written_to_the_given_file(tmp_path):
    path = tmp_path / "domain.pddl"
    model = DomainModel(LIFTED, {ON, CLEAR}, {stack()})

    text = model.to_pddl("blocks", filepath=str(path))

    assert path.read_text() == text


def test_overloaded_actions_cannot_be_exported():
    move_block = LiftedAction("move", [SignatureParameter("x", BLOCK)])
    move_small = LiftedAction("move", [SignatureParameter("x", SMALL)])
    model = DomainModel(LIFTED, set(), {move_block, move_small})

    with pytest.raises(DomainModelError, match="move"):
        model.to_pddl("d")


def test_grounded_fluents_that_flatten_to_one_symbol_cannot_be_exported():
    first = GroundedFluent("on", [PlanningObject("a_b", BLOCK)])
    second = GroundedFluent("on_a", [B])
    model = DomainModel(GROUNDED, {first, second}, set())

    with pytest.raises(DomainModelError, match="on_a_b"):
        model.to_pddl("d")


def test_grounded_actions_that_flatten_to_one_symbol_cannot_be_exported():
    first = GroundedAction("go", [PlanningObject("a_b", BLOCK)])
    second = GroundedAction("go_a", [B])
    model = DomainModel(GROUNDED, set(), {first, second})

    with pytest.raises(DomainModelError, match="go_a_b"):
        model.to_pddl("d")


def test_action_updated_into_an_invalid_state_cannot_be_exported():
    action = stack()
    model = DomainModel(LIFTED, {ON, CLEAR}, {action})

    action.add_effects.add(ParameterBoundFluent("above", [0, 1]))

    with pytest.raises(DomainModelError, match="above"):
        model.to_pddl("blocks")


def test_exported_lifted_domain_parses_with_the_pddl_library(tmp_path):
    path = tmp_path / "domain.pddl"
    DomainModel(LIFTED, {ON, CLEAR}, {stack()}, object_types=[SMALL]).to_pddl("blocks", filepath=str(path))

    domain = parse_domain(str(path))

    assert {action.name for action in domain.actions} == {"stack"}
    assert {predicate.name for predicate in domain.predicates} == {"on", "clear"}


def test_exported_grounded_domain_parses_with_the_pddl_library(tmp_path):
    path = tmp_path / "domain.pddl"
    DomainModel(GROUNDED, {ON_AB, CLEAR_B}, {grounded_stack()}).to_pddl("blocks", filepath=str(path))

    domain = parse_domain(str(path))

    assert {action.name for action in domain.actions} == {"stack_a_b"}
    assert {predicate.name for predicate in domain.predicates} == {"on_a_b", "clear_b"}


def test_action_without_preconditions_or_effects_parses_with_the_pddl_library(tmp_path):
    path = tmp_path / "domain.pddl"
    DomainModel(LIFTED, set(), {LiftedAction("wait", [])}).to_pddl("d", filepath=str(path))

    assert {action.name for action in parse_domain(str(path)).actions} == {"wait"}
