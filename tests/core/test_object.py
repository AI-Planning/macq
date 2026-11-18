from dataclasses import FrozenInstanceError

import pytest

from macq.core import CircularTypeHierarchyException, ObjectType, PlanningObject


def test_type_without_a_parent_is_a_direct_child_of_object():
    assert ObjectType("block") == ObjectType("block", ObjectType("object"))
    assert hash(ObjectType("block")) == hash(ObjectType("block", ObjectType("object")))


def test_object_is_the_root_type():
    assert ObjectType().type_name == "object"
    assert ObjectType().parent is None


def test_types_with_different_parents_are_different():
    assert ObjectType("small", ObjectType("block")) != ObjectType("small")


def test_type_is_a_subtype_of_its_ancestors_and_itself():
    block = ObjectType("block")
    small = ObjectType("small", block)

    assert small.is_subtype_of(small)
    assert small.is_subtype_of(block)
    assert small.is_subtype_of(ObjectType("object"))
    assert not block.is_subtype_of(small)


def test_type_cannot_be_its_own_ancestor():
    with pytest.raises(CircularTypeHierarchyException):
        ObjectType("a", ObjectType("b", ObjectType("a")))


def test_object_cannot_have_a_parent():
    with pytest.raises(CircularTypeHierarchyException):
        ObjectType("object", ObjectType("block"))


def test_type_is_immutable():
    with pytest.raises(FrozenInstanceError):
        ObjectType("block").type_name = "truck"


def test_planning_objects_compare_on_name_and_type():
    block = ObjectType("block")

    assert PlanningObject("a", block) == PlanningObject("a", block)
    assert hash(PlanningObject("a", block)) == hash(PlanningObject("a", block))
    assert PlanningObject("a", block) != PlanningObject("b", block)
    assert PlanningObject("a", block) != PlanningObject("a", ObjectType("truck"))


def test_planning_object_is_immutable():
    with pytest.raises(FrozenInstanceError):
        PlanningObject("a", ObjectType("block")).name = "b"
