import pytest

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
TRUCK = ObjectType("truck")
X = SignatureParameter("x", BLOCK)
Y = SignatureParameter("y", BLOCK)
ON = LiftedFluent("on", [X, Y])
ON_01 = ParameterBoundFluent("on", [0, 1])

A, B = PlanningObject("a", BLOCK), PlanningObject("b", BLOCK)
ON_AB = GroundedFluent("on", [A, B])


def stack(**contents):
    return LiftedAction("stack", [X, Y], **contents)


def test_lifted_domain_model_keeps_its_parts():
    action = stack(add_effects={ON_01})

    model = DomainModel(LIFTED, {ON}, {action})

    assert model.form is LIFTED
    assert model.fluents == {ON}
    assert model.actions == {action}


def test_grounded_domain_model_keeps_its_parts():
    action = GroundedAction("stack", [A, B], add_effects={ON_AB})

    model = DomainModel(GROUNDED, {ON_AB}, {action})

    assert model.form is GROUNDED
    assert model.fluents == {ON_AB}
    assert model.actions == {action}


@pytest.mark.parametrize("form", [LIFTED, GROUNDED])
def test_empty_domain_model_has_the_form_it_was_given(form):
    assert DomainModel(form, set(), set()).form is form


def test_empty_domain_models_of_different_forms_are_not_equal():
    assert DomainModel(LIFTED, set(), set()) != DomainModel(GROUNDED, set(), set())


def test_domain_models_with_the_same_parts_are_equal():
    first = DomainModel(LIFTED, {ON}, {stack(add_effects={ON_01})})
    second = DomainModel(LIFTED, {ON}, {stack(add_effects={ON_01})})

    assert first == second


def test_domain_models_with_different_action_contents_are_not_equal():
    assert DomainModel(LIFTED, {ON}, {stack(add_effects={ON_01})}) != DomainModel(LIFTED, {ON}, {stack()})


def test_object_types_include_those_used_and_their_ancestors():
    param = SignatureParameter("s", SMALL)

    model = DomainModel(LIFTED, set(), {LiftedAction("noop", [param])})

    assert model.object_types == {BLOCK, SMALL}


def test_declared_object_types_are_kept_even_when_unused():
    assert DomainModel(LIFTED, set(), set(), object_types=[TRUCK]).object_types == {TRUCK}


def test_form_must_be_stated():
    with pytest.raises(DomainModelError, match="form"):
        DomainModel("lifted", set(), set())


def test_contradictory_preconditions_are_allowed():
    action = stack(positive_preconditions={ON_01}, negative_preconditions={ON_01})

    assert DomainModel(LIFTED, {ON}, {action}).actions == {action}


def test_contradictory_effects_are_allowed():
    action = stack(add_effects={ON_01}, delete_effects={ON_01})

    assert DomainModel(LIFTED, {ON}, {action}).actions == {action}


def test_overloaded_lifted_actions_are_allowed():
    move_block = LiftedAction("move", [SignatureParameter("x", BLOCK)])
    move_truck = LiftedAction("move", [SignatureParameter("x", TRUCK)])

    assert len(DomainModel(LIFTED, set(), {move_block, move_truck}).actions) == 2


def test_argument_may_be_a_subtype_of_the_declared_type():
    action = LiftedAction("place", [SignatureParameter("s", SMALL), Y], add_effects={ON_01})

    assert DomainModel(LIFTED, {ON}, {action}).actions == {action}


@pytest.mark.parametrize(
    "field",
    ["positive_preconditions", "negative_preconditions", "add_effects", "delete_effects"],
)
def test_lifted_action_cannot_use_an_undeclared_predicate(field):
    action = stack(**{field: {ParameterBoundFluent("above", [0, 1])}})

    with pytest.raises(DomainModelError, match="above"):
        DomainModel(LIFTED, {ON}, {action})


def test_fluent_must_have_the_declared_number_of_arguments():
    with pytest.raises(DomainModelError, match="on"):
        DomainModel(LIFTED, {ON}, {stack(add_effects={ParameterBoundFluent("on", [0])})})


@pytest.mark.parametrize("index", [2, -1])
def test_parameter_index_must_be_in_range(index):
    with pytest.raises(DomainModelError, match=str(index)):
        DomainModel(LIFTED, {ON}, {stack(add_effects={ParameterBoundFluent("on", [0, index])})})


def test_argument_type_must_be_compatible_with_the_declared_type():
    action = LiftedAction("load", [SignatureParameter("t", TRUCK), Y], add_effects={ON_01})

    with pytest.raises(DomainModelError, match="truck"):
        DomainModel(LIFTED, {ON}, {action})


def test_argument_cannot_be_a_supertype_of_the_declared_type():
    predicate = LiftedFluent("tiny", [SignatureParameter("s", SMALL)])
    action = LiftedAction("shrink", [X], add_effects={ParameterBoundFluent("tiny", [0])})

    with pytest.raises(DomainModelError, match="tiny"):
        DomainModel(LIFTED, {predicate}, {action})


def test_predicate_cannot_be_declared_twice():
    with pytest.raises(DomainModelError, match="on"):
        DomainModel(LIFTED, {ON, LiftedFluent("on", [X])}, set())


def test_type_name_cannot_have_two_parents():
    with pytest.raises(DomainModelError, match="small"):
        DomainModel(LIFTED, set(), set(), object_types=[SMALL, ObjectType("small", TRUCK)])


def test_two_lifted_actions_cannot_share_a_signature():
    with pytest.raises(DomainModelError, match="stack"):
        DomainModel(LIFTED, {ON}, [stack(), stack(add_effects={ON_01})])


def test_two_grounded_actions_cannot_share_a_signature():
    first = GroundedAction("stack", [A, B])
    second = GroundedAction("stack", [A, B], cost=2)

    with pytest.raises(DomainModelError, match="stack"):
        DomainModel(GROUNDED, set(), [first, second])


def test_parameter_names_must_be_distinct():
    action = LiftedAction("stack", [X, SignatureParameter("X", BLOCK)])

    with pytest.raises(DomainModelError, match="stack"):
        DomainModel(LIFTED, set(), {action})


@pytest.mark.parametrize(
    "fluents, actions, object_types, clash",
    [
        ({LiftedFluent("on"), LiftedFluent("On")}, set(), (), "on"),
        (set(), {LiftedAction("move", []), LiftedAction("Move", [X])}, (), "move"),
        (set(), set(), [ObjectType("block"), ObjectType("Block")], "block"),
        (set(), set(), [ObjectType("Object")], "object"),
    ],
)
def test_names_cannot_differ_only_by_case(fluents, actions, object_types, clash):
    with pytest.raises(DomainModelError, match=f"(?i){clash}"):
        DomainModel(LIFTED, fluents, actions, object_types=object_types)


def test_grounded_object_names_cannot_differ_only_by_case():
    fluents = {GroundedFluent("clear", [A]), GroundedFluent("clear", [PlanningObject("A", BLOCK)])}

    with pytest.raises(DomainModelError, match="(?i)a"):
        DomainModel(GROUNDED, fluents, set())


def test_grounded_fluent_names_cannot_differ_only_by_case():
    with pytest.raises(DomainModelError, match="(?i)clear"):
        DomainModel(GROUNDED, {GroundedFluent("clear", [A]), GroundedFluent("Clear", [B])}, set())


def test_object_name_cannot_have_two_types():
    other = PlanningObject("a", TRUCK)

    with pytest.raises(DomainModelError, match="a"):
        DomainModel(GROUNDED, {GroundedFluent("clear", [A]), GroundedFluent("clear", [other])}, set())


@pytest.mark.parametrize(
    "field",
    ["positive_preconditions", "negative_preconditions", "add_effects", "delete_effects"],
)
def test_grounded_action_cannot_use_an_undeclared_fluent(field):
    action = GroundedAction("stack", [A, B], **{field: {ON_AB}})

    with pytest.raises(DomainModelError, match="on"):
        DomainModel(GROUNDED, set(), {action})


@pytest.mark.parametrize(
    "form, fluents, actions",
    [
        (LIFTED, {ON_AB}, set()),
        (LIFTED, {ON_01}, set()),
        (LIFTED, set(), {GroundedAction("stack", [A])}),
        (LIFTED, {ON}, {stack(add_effects={ON_AB})}),
        (GROUNDED, {ON}, set()),
        (GROUNDED, set(), {stack()}),
        (GROUNDED, {ON_AB}, {GroundedAction("stack", [A], add_effects={ON_01})}),
    ],
)
def test_parts_must_match_the_form(form, fluents, actions):
    with pytest.raises(DomainModelError, match=form.value):
        DomainModel(form, fluents, actions)


def test_details_lists_fluents_and_action_contents_in_sorted_order():
    block = ObjectType("block")
    a = PlanningObject("a", block)
    clear, held = GroundedFluent("clear", (a,)), GroundedFluent("held", (a,))
    pick = GroundedAction("pick", (a,), [clear], [held], [held], [clear])
    model = DomainModel(DomainModelForm.GROUNDED, [held, clear], [pick])

    assert model.details() == (
        "Domain model:\n"
        "  Fluents: (clear block a), (held block a)\n"
        "  Actions:\n"
        "    (pick block a):\n"
        "      precond:\n"
        "        (clear block a)\n"
        "      negative precond:\n"
        "        (held block a)\n"
        "      add:\n"
        "        (held block a)\n"
        "      delete:\n"
        "        (clear block a)\n"
    )


def test_details_omits_the_negative_precondition_section_when_there_are_none():
    model = DomainModel(DomainModelForm.GROUNDED, [], [GroundedAction("noop", ())])

    assert "negative precond" not in model.details()
