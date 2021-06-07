import pytest
from typing import List, Dict
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

# HELPER FUNCTIONS


def generate_test_fluents(num_fluents: int):
    """
    Generates basic fluents to be used for testing.

    Arguments
    ---------
    num_fluents : int
        The number of fluents to generate.

    Returns
    -------
    fluents : List of Fluents
        The list of testing fluents generated.
    """
    fluents = []
    objects = [PlanningObject("number", str(o)) for o in range(num_fluents)]
    for i in range(num_fluents):
        fluent_name = "fluent" + " " + str(i + 1)
        fluent = Fluent(fluent_name, [objects[i]])
        fluents.append(fluent)
    return fluents


def generate_fluent_dicts(fluents: List[Fluent]):
    """
    Generates fluent dictionaries to be used for testing.

    Args:
        fluents (List[Fluent]): The list of fluents to create dictionaries from.

    Returns:
        fluents_dict (dict): The dictionary of fluent names mapped to boolean values.
    """
    fluents_dict = {}
    for i in range(len(fluents)):
        if i % 2 == 0:
            fluents_dict[fluents[i]] = True
        else:
            fluents_dict[fluents[i]] = False
    return fluents_dict


def generate_test_actions(num_actions: int, objects: List[PlanningObject]):
    """
    Generates basic actions to be used for testing.

    Arguments
    ---------
    num_actions : int
        The number of actions to generate.
    objects: List of CustomObjects
        The objects available to these actions.

    Returns
    -------
    actions : List of Actions
        The list of testing actions generated.
    """
    actions = []
    for i in range(num_actions):
        action_name = "action" + " " + str(i + 1)
        # action 1 has a cost of 1, etc.
        action = Action(action_name, objects, i + 1)
        actions.append(action)
    return actions


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


def generate_test_states(num_states: int, fluents: Dict[Fluent, bool] = {}):
    """
    Generate states to be used for testing, using the given fluents (each state will add a fluent)

    Arguments
    ---------
    num_states : int
        The number of states to generate.
    fluents : dict of Fluents
        The fluents that will be used to make up the states.

    Returns
    -------
    states : List of States
        The list of testing states generated.
    """
    states = []
    next_fluents = {}
    for i in range(num_states):
        if i < len(list(fluents.keys())):
            current_fluent = list(fluents.keys())[i]
            next_fluents[current_fluent] = fluents[current_fluent]
        state = State(next_fluents.copy())
        states.append(state)
    return states


def generate_test_steps(num_steps: int, actions: List[Action], states: List[State]):
    """
    Generate steps to be used for testing, given the number of steps and possible actions and states.

    Arguments
    ---------
    num_steps : int
        The number of steps to generate.
    actions : List of Actions
        The list of possible actions to be used for the generated steps.
    states : List of States
        The list of possible states to be used for the generated steps.

    Returns
    -------
    steps : List of Steps
        The list of testing steps generated.
    """
    steps = []
    # indices for actions and states respectively
    a_index = 0
    s_index = 0
    for i in range(num_steps):
        step = Step(states[a_index], actions[s_index], i)
        # cycle through actions and states
        if a_index < len(actions):
            a_index += 1
        else:
            a_index = 0
        if s_index < len(states):
            s_index += 1
        else:
            s_index = 0
        steps.append(step)
    return steps


def generate_test_trace(complexity: int):
    """
    Generate a test trace with the given complexity (number of actions, fluents, states, and steps).

    Arguments
    ---------
    complexity : int
        The number of number of actions, fluents, states, and steps to use in this trace.

    Returns
    -------
    trace : Trace
        The testing trace generated.
    """
    fluents = generate_test_fluents(complexity)
    actions = generate_test_actions(complexity, get_fluent_obj(fluents))
    fluents_dict = generate_fluent_dicts(fluents)
    states = generate_test_states(complexity, fluents_dict)
    steps = generate_test_steps(complexity, actions, states)
    trace = Trace(steps)
    return trace


# TESTS FOR ACTION CLASS

# ensure that invalid fluents can't be added to actions.
# NOTE: DEBATING RAISING AN ERROR VS. JUST PRINTING A WARNING.
"""
def test_action_errors():
    objects = [PlanningObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    other = PlanningObject("other", "10")
    fluent_other = Fluent("put down other", [other])

    with pytest.raises(InvalidFluent):
        action.update_precond([fluent_other])
        action.update_add([fluent_other])
        action.update_delete([fluent_other])
"""


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
    assert trace.get_pre_states(action1) == [state1]
    assert trace.get_pre_states(action2) == [state2]


# test that the post states are being retrieved correctly
def test_trace_post_states():
    trace = generate_test_trace(3)
    # get the first and second action
    (action1, action2) = (trace[0].action, trace.steps[1].action)
    # get the second and last state
    (state2, state3) = (trace[1].state, trace[2].state)

    assert isinstance(action1, Action)
    assert isinstance(action2, Action)
    assert trace.get_post_states(action1) == [state2]
    assert trace.get_post_states(action2) == [state3]


# test trace SAS triples function
def test_trace_get_sas_triples():
    trace = generate_test_trace(3)
    # get the second action
    action2 = trace.steps[1].action
    # get the second and last state
    (state2, state3) = (trace.steps[1].state, trace.steps[2].state)

    assert isinstance(action2, Action)
    assert trace.get_sas_triples(action2) == [SAS(state2, action2, state3)]


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


def generate_test_trace_list(length: int):
    from random import randint

    traces = []
    for _ in range(length):
        comp = randint(1, 3)
        trace = generate_test_trace(comp)
        traces.append(trace)
    return TraceList(traces)


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
