import pytest
from typing import List
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
from macq.observation import IdentityObservation, PartialObservabilityToken
from pathlib import Path
from macq.utils.timer import TraceSearchTimeOut
from macq.generate.pddl import VanillaSampling

InvalidCostRange = Trace.InvalidCostRange
# InvalidFluent = Action.InvalidFluent
MissingGenerator = TraceList.MissingGenerator

# HELPER FUNCTIONS


def generate_test_fluents(num_fluents: int):
    """Generates basic fluents to be used for testing.

    Args:
        num_fluents (int):
            The number of fluents to generate.

    Returns:
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
    """Generates fluent dictionaries to be used for testing.

    Args:
        fluents (List[Fluent]):
            The list of fluents to create dictionaries from.

    Returns:
        The dictionary of fluent names mapped to boolean values.
    """
    fluents_dict = {}
    for i in range(len(fluents)):
        if i % 2 == 0:
            fluents_dict[fluents[i]] = True
        else:
            fluents_dict[fluents[i]] = False
    return fluents_dict


def generate_test_actions(num_actions: int):
    """Generates basic actions to be used for testing.

    Args:
    num_actions (int):
        The number of actions to generate.

    Returns:
        The list of testing actions generated.
    """
    objects = [PlanningObject("number", str(o)) for o in range(num_actions)]
    actions = []
    for i in range(num_actions):
        action_name = "action" + " " + str(i + 1)
        # action 1 has a cost of 1, etc.
        action = Action(action_name, objects, i + 1)
        actions.append(action)
    return actions


def generate_test_states(num_states: int):
    """Generate states to be used for testing, using the given fluents (each state will add a fluent)

    Args:
    num_states : (int)
        The number of states to generate.

    Returns:
        The list of testing states generated.
    """
    states = []
    next_fluents = []
    fluents = generate_test_fluents(num_states)
    for i in range(num_states):
        state_name = "state " + str(i + 1)
        next_fluents = fluents[: i + 1]
        state = State(generate_fluent_dicts(next_fluents))
        states.append(state)
    return states


def generate_test_steps(num_steps: int):
    """Generate steps to be used for testing, given the number of steps and possible actions and states.

    Args:
        num_steps (int):
            The number of steps to generate.

    Returns:
        The list of testing steps generated.
    """
    steps = []
    actions = generate_test_actions(num_steps)
    states = generate_test_states(num_steps)
    for i in range(num_steps):
        step = Step(states[i], actions[i], i + 1)
        steps.append(step)
    return steps


def generate_test_trace(complexity: int):
    """Generate a test trace with the given complexity (number of actions, fluents, states, and steps).

    Args:
        complexity (int):
            The number of number of actions, fluents, states, and steps to use in this trace.

    Returns:
        The testing trace generated.
    """
    trace = Trace(generate_test_steps(complexity))
    return trace


def get_trace_fluent_action_names(trace: Trace):
    """Retrieves the names of fluents and actions in a trace.

    Args:
        trace (Trace): the trace to extract the names from.

    Returns:
        A tuple of the names of the fluents and actions in this trace (fluent_names, action_names).
    """
    fluent_names = set()
    action_names = set()
    fluent_names.update(fluent.name for fluent in trace.fluents)
    action_names.update(action.name for action in trace.actions)
    return (fluent_names, action_names)


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

# ensure that the Trace base_fluents() and base_actions() functions work correctly
def test_trace_base():
    trace = generate_test_trace(3)
    (fluent_names, action_names) = get_trace_fluent_action_names(trace)
    assert fluent_names == {"fluent 1", "fluent 2", "fluent 3"}
    assert action_names == {"action 1", "action 2", "action 3"}


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
    # get the first and last action
    (action1, action2) = (trace[0].action, trace[1].action)
    # get the second state
    (state2, state3) = (trace[1].state, trace[2].state)

    assert isinstance(action1, Action)
    assert isinstance(action2, Action)
    assert trace.get_post_states(action1) == {state2}
    assert trace.get_post_states(action2) == {state3}


# test trace SAS triples function
def test_trace_get_sas_triples():
    trace = generate_test_trace(3)
    # get the second action
    action2 = trace[1].action
    # get the second and last state
    (state2, state3) = (trace[1].state, trace[2].state)

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
    action1 = trace[0].action
    assert isinstance(action1, Action)
    assert trace.get_usage(action1) == 1 / 3


# test trace tokenize function
def test_trace_tokenize():
    trace = generate_test_trace(3)
    (step1, step2, step3) = (trace[0], trace[1], trace[2])
    observations = trace.tokenize(IdentityObservation)
    assert observations == [
        IdentityObservation(step1),
        IdentityObservation(step2),
        IdentityObservation(step3),
    ]
    # test equality dunder by attempting to compare an object of a different type
    assert observations != step1


# test the timer wrapper on vanilla trace generation
def test_timer_wrapper_vanilla():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    dom = (base / "tests/pddl_testing_files/playlist_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/playlist_problem.pddl").resolve()
    with pytest.raises(TraceSearchTimeOut):
        VanillaSampling(dom=dom, prob=prob, plan_len=10, num_traces=5)


# generate testing trace lists
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


# test trace append function
def test_trace_append():
    trace = generate_test_trace(3)
    steps = generate_test_steps(4)
    trace.append(steps[3])
    (fluent_names, action_names) = get_trace_fluent_action_names(trace)
    assert fluent_names == {"fluent 1", "fluent 2", "fluent 3", "fluent 4"}
    assert action_names == {"action 1", "action 2", "action 3", "action 4"}
    # assert trace.steps == steps


# test trace clear function
def test_trace_clear():
    trace = generate_test_trace(3)
    trace.clear()
    assert trace.fluents == set()
    assert trace.actions == set()
    assert trace.steps == []


# test trace extend function
def test_trace_extend():
    trace = generate_test_trace(3)
    steps = generate_test_steps(7)
    trace.extend(steps[3:])
    (fluent_names, action_names) = get_trace_fluent_action_names(trace)
    assert fluent_names == {
        "fluent 1",
        "fluent 2",
        "fluent 3",
        "fluent 4",
        "fluent 5",
        "fluent 6",
        "fluent 7",
    }

    assert action_names == {
        "action 1",
        "action 2",
        "action 3",
        "action 4",
        "action 5",
        "action 6",
        "action 7",
    }

    # assert trace.steps == steps


# test trace insert function
def test_trace_insert():
    trace = generate_test_trace(3)
    steps = generate_test_steps(4)
    trace.insert(0, steps[3])
    (fluent_names, action_names) = get_trace_fluent_action_names(trace)
    assert fluent_names == {"fluent 1", "fluent 2", "fluent 3", "fluent 4"}
    assert action_names == {"action 1", "action 2", "action 3", "action 4"}
    # assert trace.steps == [steps[3], steps[0], steps[1], steps[2]]


# test trace pop function
def test_trace_pop():
    trace = generate_test_trace(3)
    steps = trace.steps.copy()
    trace.pop()
    (fluent_names, action_names) = get_trace_fluent_action_names(trace)
    assert fluent_names == {"fluent 1", "fluent 2"}
    assert action_names == {"action 1", "action 2"}
    # assert trace == steps[:-1]


# test trace remove function
def test_trace_remove():
    trace = generate_test_trace(3)
    steps = trace.steps.copy()
    trace.remove(steps[1])
    (fluent_names, action_names) = get_trace_fluent_action_names(trace)
    assert fluent_names == {"fluent 1", "fluent 2", "fluent 3"}
    assert action_names == {"action 1", "action 3"}
    # assert trace.steps == [steps[0], steps[2]]


if __name__ == "__main__":
    state = generate_test_states(1)[0]
    fluents = state.keys()
    print(fluents)

    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=1, num_traces=1)
    # print(vanilla.traces)
    # vanilla = VanillaSampling(problem_id=123, plan_len=5, num_traces=5)
    # print(vanilla.traces)

    # test tokenization
    random_tokens = vanilla.traces[0].tokenize(
        PartialObservabilityToken,
        method=PartialObservabilityToken.random_subset,
        percent_missing=50,
    )

    hide_fluents = list(vanilla.traces[0].fluents)[:2]
    print("hiding: " + str(hide_fluents))
    same_tokens = vanilla.traces[0].tokenize(
        PartialObservabilityToken,
        method=PartialObservabilityToken.same_subset,
        hide_fluents=hide_fluents,
    )

    # for token in random_tokens:
    #     print(token.index)
    #     print(token.step)
    #     print()
