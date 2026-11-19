from macq.core import GroundedAction, ObjectType, PlanningObject
from macq.trace.action import AtomicAction
from tests.utils.generators import generate_test_actions


def test_action():
    a1, a2 = generate_test_actions(2)

    assert a1 == GroundedAction(a1.name, a1.objects, cost=a1.cost)
    assert a1 != a2
    assert str(a1)


def test_atomic_action_keeps_the_trace_text():
    block = ObjectType("block")
    action = GroundedAction("stack", [PlanningObject("a", block), PlanningObject("b", block)], cost=None)

    atomic = AtomicAction.of(action)

    assert str(atomic) == "stack block a block b"
    assert atomic.obj_params == ["block a", "block b"]
    assert atomic == AtomicAction("stack", ["block a", "block b"])
    assert atomic.cost is None
