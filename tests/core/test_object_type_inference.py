from macq.core import GroundedAction, GroundedFluent, ObjectType, PlanningObject, infer_object_types_from_actions, infer_object_types_from_fluents
from macq.trace import State, Step, Trace, TraceList
from macq.observation import IdentityObservation  # isort: skip (macq.trace must load first)

T1, T2, L1, L2 = (PlanningObject(n, ObjectType()) for n in ("t1", "t2", "l1", "l2"))


def observed_traces():
    state = State({GroundedFluent("at", [T1, L1]): True, GroundedFluent("at", [T2, L2]): True})
    steps = [
        Step(state, GroundedAction("wait", [T1]), 1),
        Step(state, GroundedAction("wait", [T2]), 2),
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
    inferred = infer_object_types_from_fluents(observed_traces())

    assert groups(inferred) == [{"l1", "l2"}, {"t1", "t2"}]


def test_supplied_true_fluents_decide_the_types():
    true_fluents = {GroundedFluent("at", [T1, L1]), GroundedFluent("at", [T2, L1])}

    inferred = infer_object_types_from_fluents(observed_traces(), true_fluents)

    assert groups(inferred) == [{"l1"}, {"l2"}, {"t1", "t2"}]


def test_objects_in_the_same_action_position_share_a_type():
    actions = {GroundedAction("drive", [T1, L1]), GroundedAction("drive", [T2, L2])}

    assert groups(infer_object_types_from_actions(actions)) == [{"l1", "l2"}, {"t1", "t2"}]


def test_inferred_types_are_flat():
    inferred = infer_object_types_from_fluents(observed_traces())

    assert len(set(inferred.values())) == 2
    assert all(isinstance(object_type, str) for object_type in inferred.values())
