import pytest
from macq.trace import *
from macq.observation import IdentityObservation
from tests.utils.generators import generate_test_steps, generate_test_trace

InvalidCostRange = Trace.InvalidCostRange

# test the functionality to add steps to a trace (NOT YET WORKING -- need equality dunders). pass for now
def test_trace_add_steps():
    """
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    fluent = Fluent("on table", [objects[0]], True)
    state = State([fluent])
    trace = generate_test_trace(3)
    step4 = generate_test_steps(1, [action], [state])

    result = copy.deepcopy(trace.steps)
    result.append(step4)

    trace.add_steps([step4])
    assert trace.steps == result
    """
    pass


# test that the previous states are being retrieved correctly
def test_trace_pre_states():
    trace = generate_test_trace(3)
    # get the first and last action
    (action1, action2) = (trace[0].action, trace[1].action)
    # get the first and last state
    (state1, state2) = (trace[0].state, trace[1].state)

    assert isinstance(action1, Action)
    assert isinstance(action2, Action)
    assert trace.get_pre_states(action1) == {state1}
    assert trace.get_pre_states(action2) == {state2}


# test that the post states are being retrieved correctly
def test_trace_post_states():
    trace = generate_test_trace(3)
    # get the first and second action
    (action1, action2) = (trace[0].action, trace.steps[1].action)
    # get the second and last state
    (state2, state3) = (trace[1].state, trace[2].state)

    assert isinstance(action1, Action)
    assert isinstance(action2, Action)
    assert trace.get_post_states(action1) == {state2}
    assert trace.get_post_states(action2) == {state3}


# test trace SAS triples function
def test_trace_get_sas_triples():
    trace = generate_test_trace(3)
    # get the second action
    action2 = trace.steps[1].action
    # get the second and last state
    (state2, state3) = (trace.steps[1].state, trace.steps[2].state)

    assert isinstance(action2, Action)
    assert trace.get_sas_triples(action2) == {SAS(state2, action2, state3)}


# test that the total cost is working correctly
def test_trace_total_cost():
    trace = generate_test_trace(5)
    assert trace.get_total_cost() == 10


# test that the cost range is working correctly
def test_trace_valid_cost_range():
    trace = generate_test_trace(5)
    assert trace.get_slice_cost(1, 3) == 6
    assert trace.get_slice_cost(2, 3) == 5
    assert trace.get_slice_cost(1, 5) == 10
    assert trace.get_slice_cost(4, 5) == 4


# test that incorrect provided cost ranges throw errors
def test_trace_invalid_cost_range():
    trace = generate_test_trace(3)
    with pytest.raises(InvalidCostRange):
        trace.get_slice_cost(-2, 2)

    with pytest.raises(InvalidCostRange):
        trace.get_slice_cost(3, 1)


# test trace action usage
def test_trace_usage():
    trace = generate_test_trace(3)
    # get the first action
    action1 = trace.steps[0].action
    assert isinstance(action1, Action)
    assert trace.get_usage(action1) == 1 / 3


# test trace tokenize function
def test_trace_tokenize():
    trace = generate_test_trace(3)
    (step1, step2, step3) = (trace.steps[0], trace.steps[1], trace.steps[2])
    observations = trace.tokenize(IdentityObservation)
    assert observations == [
        IdentityObservation(step1),
        IdentityObservation(step2),
        IdentityObservation(step3),
    ]
    # test equality dunder by attempting to compare an object of a different type
    assert observations != step1


def test_trace_rep():
    trace = generate_test_trace(3)
    assert trace.details()


def test_trace_list_methods():
    trace = generate_test_trace(3)
    steps = generate_test_steps(3)
    step = steps[0]

    trace[0] = step
    assert trace.count(step) == 1
    assert trace.index(step) == 0
    trace.insert(0, step)
    assert trace[0] is step
    del trace[0]
    del trace[0]
    assert trace[0] != step
    assert step not in trace

    rev = list(reversed(trace))
    trace.reverse()
    assert trace.steps == rev
    assert trace.pop() not in trace
    assert trace.steps == trace.copy()

    trace.extend(steps)
    for s in steps:
        assert s in trace

    trace.remove(step)
    assert step not in trace
