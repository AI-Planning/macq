from macq.trace import PlanningObject, Fluent, Action, Step, State, Trace, TraceList
from macq.observation import IdentityObservation
from macq.generate.pddl import VanillaSampling

InvalidCostRange = Trace.InvalidCostRange
MissingGenerator = TraceList.MissingGenerator

from typing import List
from pathlib import Path
import pytest

# HELPER FUNCTIONS


def get_fluent_obj(fluents: List[Fluent]):
    """
    Extracts the objects used by the given fluents.

    Arguments
    ---------
    fluents : List of Fluents
        The fluents to extract the objects from.

    Returns
    -------
    objects : List of PlanningObjects
        The list of objects used by the given fluents.
    """
    objects = []
    for fluent in fluents:
        for obj in fluent.objects:
            objects.append(obj)
    return objects


# ensure that valid object parameters can be added and subsequently referenced
def test_action_add_params():
    objects = [PlanningObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    other = PlanningObject("other", 10)
    fluent_other = Fluent("put down other", [other], True)

    action.add_parameter(other)


# TESTS FOR TRACE CLASS

# ensure that the Trace base_fluents() and base_actions() functions work correctly
def test_trace_base():
    trace = generate_test_trace(3)
    print(trace.fluents)
    print(trace.actions)
    assert trace.fluents == ["fluent 1", "fluent 2", "fluent 3"]
    assert trace.actions == ["action 1", "action 2", "action 3"]


# test that the previous states are being retrieved correctly
def test_trace_prev_states():
    trace = generate_test_trace(3)
    # get the first and last action
    (action1, action3) = (trace.steps[0].action, trace.steps[2].action)
    # get the first and last state
    (state1, state3) = (trace.steps[0].state, trace.steps[2].state)

    assert trace.get_prev_states(action1) == [state1]
    assert trace.get_prev_states(action3) == [state3]


# test that the post states are being retrieved correctly
def test_trace_post_states():
    trace = generate_test_trace(3)
    # get the first and last action
    (action1, action3) = (trace.steps[0].action, trace.steps[2].action)
    # get the second state
    state2 = trace.steps[1].state

    assert trace.get_post_states(action1) == [state2]
    assert trace.get_post_states(action3) == []


# test trace SAS triples function
def test_trace_get_sas_triples():
    trace = generate_test_trace(3)
    # get the second and last action
    (action2, action3) = (trace.steps[1].action, trace.steps[2].action)
    # get the second and last state
    (state2, state3) = (trace.steps[1].state, trace.steps[2].state)

    assert trace.get_sas_triples(action2) == [(state2, action2, state3)]
    assert trace.get_sas_triples(action3) == [(state3, action3)]


# test that the total cost is working correctly
def test_trace_total_cost():
    trace = generate_test_trace(5)
    assert trace.get_total_cost() == 15


# test that the cost range is working correctly
def test_trace_valid_cost_range():
    trace = generate_test_trace(5)
    assert trace.get_cost_range(1, 3) == 6
    assert trace.get_cost_range(2, 3) == 5
    assert trace.get_cost_range(1, 5) == 15
    assert trace.get_cost_range(4, 5) == 9


# test that incorrect provided cost ranges throw errors
def test_trace_invalid_cost_range():
    trace = generate_test_trace(3)
    with pytest.raises(InvalidCostRange):
        trace.get_cost_range(3, 1)
        trace.get_cost_range(0, 2)
        trace.get_cost_range(1, 5)


# test trace action usage
def test_trace_usage():
    trace = generate_test_trace(3)
    # get the first action
    action1 = trace.steps[0].action
    assert trace.get_usage(action1) == 1 / 3


# test trace tokenize function
def test_trace_tokenize():
    trace = generate_test_trace(3)
    (step1, step2, step3) = (trace.steps[0], trace.steps[1], trace.steps[2])
    trace.tokenize(IdentityObservation)
    print(trace.observations)
    print(
        [
            IdentityObservation(step1),
            IdentityObservation(step2),
            IdentityObservation(step3),
        ]
    )
    assert trace.observations == [
        IdentityObservation(step1),
        IdentityObservation(step2),
        IdentityObservation(step3),
    ]
    # test equality dunder by attempting to compare an object of a different type
    assert trace.observations != step1


# generate testing trace lists
def generate_test_trace_list(length: int):
    trace = generate_test_trace(3)
    traces = [trace] * length
    return TraceList(traces)


# test trace lists
def test_trace_list():
    trace_list = generate_test_trace_list(5)

    assert len(trace_list) == 5

    with pytest.raises(MissingGenerator):
        trace_list.generate_more(5)

    first = trace_list[0]
    trace_list.generator = generate_test_trace_list
    trace_list.generate_more(5)
    assert len(trace_list) == 10
    assert trace_list[0] is first

    action = trace_list[0].steps[0].action
    usages = trace_list.get_usage(action)
    for i, trace in enumerate(trace_list):
        assert usages[i] == trace.get_usage(action)


# test trace append function
def test_trace_append():
    trace = generate_test_trace(3)
    steps = generate_test_steps(4)
    trace.append(steps[3])
    assert trace.fluents == ["fluent 1", "fluent 2", "fluent 3", "fluent 4"]
    assert trace.actions == ["action 1", "action 2", "action 3", "action 4"]
    # assert trace.steps == steps


# test trace clear function
def test_trace_clear():
    trace = generate_test_trace(3)
    trace.clear()
    assert trace.fluents == []
    assert trace.actions == []
    assert trace.steps == []


# test trace extend function
def test_trace_extend():
    trace = generate_test_trace(3)
    steps = generate_test_steps(7)
    trace.extend(steps[3:])
    assert trace.fluents == [
        "fluent 1",
        "fluent 2",
        "fluent 3",
        "fluent 4",
        "fluent 5",
        "fluent 6",
        "fluent 7",
    ]
    assert trace.actions == [
        "action 1",
        "action 2",
        "action 3",
        "action 4",
        "action 5",
        "action 6",
        "action 7",
    ]
    # assert trace.steps == steps


# test trace insert function
def test_trace_insert():
    trace = generate_test_trace(3)
    steps = generate_test_steps(4)
    trace.insert(0, steps[3])
    assert trace.fluents == ["fluent 1", "fluent 2", "fluent 3", "fluent 4"]
    assert trace.actions == ["action 1", "action 2", "action 3", "action 4"]
    # assert trace.steps == [steps[3], steps[0], steps[1], steps[2]]


# test trace pop function
def test_trace_pop():
    trace = generate_test_trace(3)
    steps = trace.steps.copy()
    trace.pop()
    assert trace.fluents == ["fluent 1", "fluent 2"]
    assert trace.actions == ["action 1", "action 2"]
    # assert trace.steps == steps[:-1]


# test trace remove function
def test_trace_remove():
    trace = generate_test_trace(3)
    steps = trace.steps.copy()
    trace.remove(steps[1])
    assert trace.fluents == ["fluent 1", "fluent 2", "fluent 3"]
    assert trace.actions == ["action 1", "action 3"]
    # assert trace.steps == [steps[0], steps[2]]


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    dom = (base / "tests/pddl_testing_files/playlist_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/playlist_problem.pddl").resolve()
    # vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=2, num_traces=1)
    # print(vanilla.traces)
    vanilla = VanillaSampling(problem_id=100, plan_len=3, num_traces=1)
    print(vanilla.traces)
