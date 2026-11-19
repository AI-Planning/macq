from macq.core import GroundedAction, GroundedFluent, ObjectType, PlanningObject
from macq.trace import State, Step, Trace

A = PlanningObject("a", ObjectType("block"))
ON = GroundedFluent("clear", [A])


def step(value=True, action="pick", index=1):
    return Step(State({ON: value}), GroundedAction(action, [A]), index)


def test_steps_compare_on_state_action_and_index():
    assert step() == step()
    assert step() != step(value=False)
    assert step() != step(action="drop")
    assert step() != step(index=2)


def test_traces_compare_on_their_steps():
    assert Trace([step(index=1), step(index=2)]) == Trace([step(index=1), step(index=2)])
    assert Trace([step(index=1)]) != Trace([step(index=1, value=False)])


def test_a_trace_finds_an_equal_step_at_its_own_index():
    trace = Trace([step(index=1), step(index=2)])
    assert trace.index(step(index=2)) == 1
    assert step(index=3) not in trace
