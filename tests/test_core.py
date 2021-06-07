import pytest
from typing import List, Dict
from tests.utils.generators import *
from macq.trace import (
    PlanningObject,
    Fluent,
    Action,
    Step,
    State,
    Trace,
    SAS,
    TraceList,
)
from macq.observation import IdentityObservation
from pathlib import Path
from macq.utils.timer import TraceSearchTimeOut
from macq.generate.pddl import VanillaSampling

InvalidCostRange = Trace.InvalidCostRange
# InvalidFluent = Action.InvalidFluent
MissingGenerator = TraceList.MissingGenerator


def get_fluent_obj(fluents: List[Fluent]):
    """
    Extracts the objects used by the given fluents.

    Arguments
    ---------
    fluents : List of Fluents
        The fluents to extract the objects from.

    Returns
    -------
    objects : List of CustomObjects
        The list of objects used by the given fluents.
    """
    objects = []
    for fluent in fluents:
        for obj in fluent.objects:
            objects.append(obj)
    return objects


# ensure that valid object parameters can be added and subsequently referenced
# def test_action_add_params():
#     objects = [PlanningObject("number", str(o)) for o in range(6)]
#     action = Action("put down", objects, 1)
#     other = PlanningObject("other", "other")
#     fluent_other = Fluent("put down other", [other])

#     action.add_parameter(other)
# action.update_precond([fluent_other])
# action.update_add([fluent_other])
# action.update_delete([fluent_other])
# assert action.precond == {fluent_other}
# assert action.add == {fluent_other}
# assert action.delete == {fluent_other}


# TESTS FOR TRACE CLASS

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
    assert trace.get_total_cost() == 15


# test that the cost range is working correctly
def test_trace_valid_cost_range():
    trace = generate_test_trace(5)
    assert trace.get_slice_cost(1, 3) == 6
    assert trace.get_slice_cost(2, 3) == 5
    assert trace.get_slice_cost(1, 5) == 15
    assert trace.get_slice_cost(4, 5) == 9


# test that incorrect provided cost ranges throw errors
def test_trace_invalid_cost_range():
    trace = generate_test_trace(3)
    with pytest.raises(InvalidCostRange):
        trace.get_slice_cost(3, 1)
        trace.get_slice_cost(0, 2)
        trace.get_slice_cost(1, 5)


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


# test the timer wrapper on vanilla trace generation
# def test_timer_vanilla_wrapper():
#     # exit out to the base macq folder so we can get to /tests
#     base = Path(__file__).parent.parent
#     dom = (base / "tests/pddl_testing_files/playlist_domain.pddl").resolve()
#     prob = (base / "tests/pddl_testing_files/playlist_problem.pddl").resolve()

#     with pytest.raises(TraceSearchTimeOut):
#         VanillaSampling(dom, prob, 10, 5)


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
