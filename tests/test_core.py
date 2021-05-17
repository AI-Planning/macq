from macq.trace import CustomObject, Fluent, Action, Step, State, Trace
from macq.observation import IdentityObservation

InvalidCostRange = Trace.InvalidCostRange
InvalidFluent = Action.InvalidFluent

from typing import List
import pytest

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
    objects = [CustomObject("number", str(o)) for o in range(num_fluents)]
    for i in range(num_fluents):
        fluent_name = "fluent" + " " + str(i + 1)
        if i % 2 == 0:
            value = True
        else:
            value = False
        fluent = Fluent(fluent_name, [objects[i]], value)
        fluents.append(fluent)
    return fluents

def generate_test_actions(num_actions: int, objects: List[CustomObject]):
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
        action = Action(action_name, objects, [], [], [], i + 1)
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

def generate_test_states(num_states: int, fluents: List[Fluent]):
    """
    Generate states to be used for testing, using the given fluents (each state will add a fluent)

    Arguments
    ---------
    num_states : int
        The number of states to generate.
    fluents : List of Fluents
        The fluents that will be used to make up the states.

    Returns
    -------
    states : List of States
        The list of testing states generated.
    """
    states = []
    next_fluents = []
    for i in range(num_states):
        state_name = "state" + " " + str(i + 1)
        if i < len(fluents):
            next_fluents.append(fluents[i])
        state = State(next_fluents)
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
    for _ in range(num_steps):
        step = Step(actions[a_index], states[s_index])
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
    states = generate_test_states(complexity, fluents)
    steps = generate_test_steps(complexity, actions, states)
    trace = Trace(steps)
    return trace


# TESTS FOR ACTION CLASS

# ensure that invalid fluents can't be added to actions
def test_action_errors():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    other = CustomObject("other", 10)
    fluent_other = Fluent("put down other", [other], True)

    with pytest.raises(InvalidFluent):
        action.add_precond([fluent_other])
        action.add_effect_add([fluent_other])
        action.add_effect_delete([fluent_other])


# ensure that valid fluents can be added as action preconditions
def test_action_add_preconditions():
    fluents = generate_test_fluents(3)
    (fl1, fl2, fl3) = tuple(fluents)
    action = Action("put down", get_fluent_obj(fluents), [], [], [], 1)

    action.add_precond([fl1])
    assert action.precond == [fl1]
    action.add_precond([fl2, fl3])
    assert action.precond == [fl1, fl2, fl3]


# ensure that valid fluents can be added as action effects
def test_action_add_effects():
    fluents = generate_test_fluents(6)
    (fl1, fl2, fl3, fl4, fl5, fl6) = tuple(fluents)
    action = Action("put down", get_fluent_obj(fluents), [], [], [], 1)

    action.add_effect_add([fl4])
    assert action.add == [fl4]
    action.add_effect_add([fl5, fl6])
    assert action.add == [fl4, fl5, fl6]
    action.add_effect_delete([fl1])
    assert action.delete == [fl1]
    action.add_effect_delete([fl2, fl3])
    assert action.delete == [fl1, fl2, fl3]


# ensure that valid object parameters can be added and subsequently referenced
def test_action_add_params():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    other = CustomObject("other", 10)
    fluent_other = Fluent("put down other", [other], True)

    action.add_parameter(other)
    action.add_precond([fluent_other])
    action.add_effect_add([fluent_other])
    action.add_effect_delete([fluent_other])
    assert action.precond == [fluent_other]
    assert action.add == [fluent_other]
    assert action.delete == [fluent_other]


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


# ensure that the Trace base_fluents() and base_actions() functions work correctly
def test_trace_base():
    trace = generate_test_trace(3)
    assert trace.base_fluents() == ["fluent 1", "fluent 2", "fluent 3"]
    assert trace.base_actions() == ["action 1", "action 2", "action 3"]


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
