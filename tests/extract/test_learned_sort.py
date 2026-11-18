from macq.extract.learned_sort import (
    Sort,
    sort_inference_by_action,
    sort_inference_by_fluents,
)
from macq.observation import IdentityObservation
from macq.trace import Action, Fluent, PlanningObject, State, Step, Trace, TraceList

T1, T2, L1, L2 = (PlanningObject("object", n) for n in ("t1", "t2", "l1", "l2"))


def observed_traces():
    state = State({Fluent("at", [T1, L1]): True, Fluent("at", [T2, L2]): True})
    steps = [
        Step(state, Action("wait", [T1]), 1),
        Step(state, Action("wait", [T2]), 2),
        Step(state, None, 3),
    ]
    return TraceList([Trace(steps)]).tokenize(IdentityObservation)


def groups(object_types):
    """Groups objects by inferred type, since the type names are arbitrary."""
    by_type = {}
    for obj, object_type in object_types.items():
        by_type.setdefault(object_type, set()).add(obj)
    return sorted(by_type.values(), key=sorted)


def test_objects_in_the_same_fluent_position_share_a_type():
    inferred = sort_inference_by_fluents(observed_traces())

    assert groups(inferred) == [{"l1", "l2"}, {"t1", "t2"}]


def test_supplied_true_fluents_decide_the_types():
    true_fluents = {Fluent("at", [T1, L1]), Fluent("at", [T2, L1])}

    inferred = sort_inference_by_fluents(observed_traces(), true_fluents)

    assert groups(inferred) == [{"l1"}, {"l2"}, {"t1", "t2"}]


def test_objects_in_the_same_action_position_share_a_type():
    actions = {Action("drive", [T1, L1]), Action("drive", [T2, L2])}

    assert groups(sort_inference_by_action(actions)) == [{"l1", "l2"}, {"t1", "t2"}]


def test_inferred_types_are_flat():
    inferred = sort_inference_by_fluents(observed_traces())

    assert len(set(inferred.values())) == 2
    assert all(isinstance(object_type, str) for object_type in inferred.values())


def test_type_is_not_equal_to_a_non_type():
    assert Sort("truck") != "truck"


def test_types_with_the_same_name_and_parent_are_equal():
    assert Sort("truck", "vehicle") == Sort("truck", "vehicle")
    assert Sort("truck", "vehicle") != Sort("truck", "thing")
