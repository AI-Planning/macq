import json

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
CLEAR = LiftedFluent("clear", [X])
ON_10 = ParameterBoundFluent("on", [1, 0])
CLEAR_1 = ParameterBoundFluent("clear", [1])

A, B = PlanningObject("a", BLOCK), PlanningObject("b", SMALL)
ON_AB = GroundedFluent("on", [A, B])
CLEAR_B = GroundedFluent("clear", [B])

LIFTED_DOCUMENT = {
    "format_version": 1,
    "form": "lifted",
    "object_types": [{"name": "block", "parent": "object"}, {"name": "small", "parent": "block"}],
    "fluents": [
        {"name": "clear", "parameters": [{"name": "x", "type": "block"}]},
        {"name": "on", "parameters": [{"name": "x", "type": "block"}, {"name": "y", "type": "block"}]},
    ],
    "actions": [
        {
            "name": "stack",
            "parameters": [{"name": "x", "type": "block"}, {"name": "y", "type": "block"}],
            "positive_preconditions": [{"name": "clear", "arguments": [1]}],
            "negative_preconditions": [{"name": "on", "arguments": [1, 0]}],
            "add_effects": [{"name": "on", "arguments": [1, 0]}],
            "delete_effects": [{"name": "clear", "arguments": [1]}],
        }
    ],
}

GROUNDED_DOCUMENT = {
    "format_version": 1,
    "form": "grounded",
    "object_types": [{"name": "block", "parent": "object"}, {"name": "small", "parent": "block"}],
    "objects": [{"name": "a", "type": "block"}, {"name": "b", "type": "small"}],
    "fluents": [{"name": "clear", "arguments": ["b"]}, {"name": "on", "arguments": ["a", "b"]}],
    "actions": [
        {
            "name": "stack",
            "arguments": ["a", "b"],
            "cost": 3,
            "positive_preconditions": [{"name": "clear", "arguments": ["b"]}],
            "negative_preconditions": [{"name": "on", "arguments": ["a", "b"]}],
            "add_effects": [{"name": "on", "arguments": ["a", "b"]}],
            "delete_effects": [{"name": "clear", "arguments": ["b"]}],
        }
    ],
}


def lifted_model():
    action = LiftedAction(
        "stack",
        [X, Y],
        positive_preconditions={CLEAR_1},
        negative_preconditions={ON_10},
        add_effects={ON_10},
        delete_effects={CLEAR_1},
    )
    return DomainModel(LIFTED, {ON, CLEAR}, {action}, object_types=[SMALL])


def grounded_model():
    action = GroundedAction(
        "stack",
        [A, B],
        positive_preconditions={CLEAR_B},
        negative_preconditions={ON_AB},
        add_effects={ON_AB},
        delete_effects={CLEAR_B},
        cost=3,
    )
    return DomainModel(GROUNDED, {ON_AB, CLEAR_B}, {action})


def without(document, key):
    return {name: value for name, value in document.items() if name != key}


def test_lifted_domain_model_serializes_to_the_documented_format():
    assert json.loads(lifted_model().serialize()) == LIFTED_DOCUMENT


def test_grounded_domain_model_serializes_to_the_documented_format():
    assert json.loads(grounded_model().serialize()) == GROUNDED_DOCUMENT


def test_lifted_domain_model_is_read_from_the_documented_format():
    assert DomainModel.deserialize(json.dumps(LIFTED_DOCUMENT)) == lifted_model()


def test_grounded_domain_model_is_read_from_the_documented_format():
    assert DomainModel.deserialize(json.dumps(GROUNDED_DOCUMENT)) == grounded_model()


@pytest.mark.parametrize(
    "model",
    [
        DomainModel(LIFTED, set(), set()),
        DomainModel(GROUNDED, set(), set()),
        DomainModel(LIFTED, set(), set(), object_types=[SMALL, TRUCK]),
        DomainModel(LIFTED, set(), {LiftedAction("wait", [SignatureParameter("x")])}),
        DomainModel(
            LIFTED,
            set(),
            {
                LiftedAction("move", [SignatureParameter("x", BLOCK)]),
                LiftedAction("move", [SignatureParameter("x", TRUCK)]),
            },
        ),
        DomainModel(
            LIFTED,
            {ON},
            {
                LiftedAction(
                    "odd",
                    [X, Y],
                    positive_preconditions={ON_10},
                    negative_preconditions={ON_10},
                    add_effects={ON_10},
                    delete_effects={ON_10},
                )
            },
        ),
        DomainModel(GROUNDED, set(), {GroundedAction("wait", [])}),
    ],
)
def test_domain_model_survives_a_round_trip(model):
    assert DomainModel.deserialize(model.serialize()) == model


def test_output_does_not_depend_on_input_order():
    first = DomainModel(LIFTED, [ON, CLEAR], [LiftedAction("b", [X]), LiftedAction("a", [X])])
    second = DomainModel(LIFTED, [CLEAR, ON], [LiftedAction("a", [X]), LiftedAction("b", [X])])

    assert first.serialize() == second.serialize()


def test_serialized_text_is_written_to_the_given_file(tmp_path):
    path = tmp_path / "model.json"

    text = lifted_model().serialize(filepath=str(path))

    assert path.read_text() == text


def test_action_updated_into_an_invalid_state_cannot_be_serialized():
    action = LiftedAction("stack", [X, Y])
    model = DomainModel(LIFTED, {ON}, {action})

    action.add_effects.add(ParameterBoundFluent("above", [0, 1]))

    with pytest.raises(DomainModelError, match="above"):
        model.serialize()


def test_unknown_format_version_is_rejected():
    with pytest.raises(DomainModelError, match="version"):
        DomainModel.deserialize(json.dumps({**LIFTED_DOCUMENT, "format_version": 2}))


def test_missing_format_version_is_rejected():
    with pytest.raises(DomainModelError, match="version"):
        DomainModel.deserialize(json.dumps(without(LIFTED_DOCUMENT, "format_version")))


def test_invalid_json_is_rejected():
    with pytest.raises(DomainModelError, match="JSON"):
        DomainModel.deserialize("{not json")


@pytest.mark.parametrize("key", ["form", "object_types", "fluents", "actions"])
def test_missing_section_is_rejected(key):
    with pytest.raises(DomainModelError, match=key):
        DomainModel.deserialize(json.dumps(without(LIFTED_DOCUMENT, key)))


def test_unknown_form_is_rejected():
    with pytest.raises(DomainModelError, match="partial"):
        DomainModel.deserialize(json.dumps({**LIFTED_DOCUMENT, "form": "partial"}))


def test_unknown_parent_type_is_rejected():
    document = {**LIFTED_DOCUMENT, "object_types": [{"name": "small", "parent": "block"}]}

    with pytest.raises(DomainModelError, match="block"):
        DomainModel.deserialize(json.dumps(document))


def test_cycle_in_object_types_is_rejected():
    types = [{"name": "a", "parent": "b"}, {"name": "b", "parent": "a"}]
    document = {**LIFTED_DOCUMENT, "object_types": types, "fluents": [], "actions": []}

    with pytest.raises(DomainModelError, match="(?i)cycle"):
        DomainModel.deserialize(json.dumps(document))


def test_type_listed_twice_is_rejected():
    types = [{"name": "a", "parent": "object"}, {"name": "a", "parent": "object"}]
    document = {**LIFTED_DOCUMENT, "object_types": types, "fluents": [], "actions": []}

    with pytest.raises(DomainModelError, match="'a'"):
        DomainModel.deserialize(json.dumps(document))


def test_unknown_object_is_rejected():
    document = {**GROUNDED_DOCUMENT, "fluents": [{"name": "clear", "arguments": ["z"]}], "actions": []}

    with pytest.raises(DomainModelError, match="'z'"):
        DomainModel.deserialize(json.dumps(document))


def test_document_describing_a_malformed_domain_model_is_rejected():
    with pytest.raises(DomainModelError, match="clear"):
        DomainModel.deserialize(json.dumps({**LIFTED_DOCUMENT, "fluents": LIFTED_DOCUMENT["fluents"][1:]}))
