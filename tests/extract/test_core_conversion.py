import pytest

from macq.core import DomainModelError, GroundedFluent, ObjectType, PlanningObject
from macq.extract._core_conversion import to_grounded_fluent, to_planning_object

BLOCK_A = PlanningObject("a", ObjectType("block"))
BLOCK_B = PlanningObject("b", ObjectType("block"))


def test_converts_trace_and_text_objects():
    assert to_planning_object(PlanningObject("a", ObjectType("block"))) == BLOCK_A
    assert to_planning_object("block a") == BLOCK_A


def test_flattens_a_trace_object_type_to_its_name():
    truck = ObjectType("truck", ObjectType("vehicle"))
    assert to_planning_object(PlanningObject("t1", truck)) == PlanningObject("t1", ObjectType("truck"))


def test_converts_trace_and_text_fluents():
    expected = GroundedFluent("on", (BLOCK_A, BLOCK_B))
    trace_objects = [PlanningObject("a", ObjectType("block")), PlanningObject("b", ObjectType("block"))]
    assert to_grounded_fluent(GroundedFluent("on", trace_objects)) == expected
    assert to_grounded_fluent("(on block a block b)") == expected


def test_converts_a_fluent_without_objects():
    assert to_grounded_fluent("(handempty)") == GroundedFluent("handempty")


@pytest.mark.parametrize("text", ["on block a", "(on block)", "()", "(on block a block)"])
def test_rejects_malformed_fluent_text(text):
    with pytest.raises(DomainModelError):
        to_grounded_fluent(text)


@pytest.mark.parametrize("text", ["a", "block a extra"])
def test_rejects_malformed_object_text(text):
    with pytest.raises(DomainModelError):
        to_planning_object(text)
