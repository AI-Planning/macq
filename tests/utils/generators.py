from macq.trace import *
from macq.observation import IdentityObservation
from macq.extract import Extract, modes


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
    objects = [PlanningObject("number", str(o)) for o in range(num_fluents)]
    return {
        Fluent(f"fluent {str(i+1)}", [objects[i]]): i % 2 for i in range(num_fluents)
    }


def generate_test_actions(num_actions: int):
    """
    Generates basic actions to be used for testing.

    Arguments
    ---------
    num_actions : int
        The number of actions to generate.

    Returns
    -------
    actions : List of Actions
        The list of testing actions generated.
    """
    objects = [PlanningObject("number", str(o)) for o in range(num_actions)]
    actions = []
    for i in range(num_actions):
        action_name = "action " + str(i + 1)
        # action 1 has a cost of 1, etc.
        action = Action(action_name, objects, i + 1)
        actions.append(action)
    return actions


def generate_test_states(num_states: int):
    """
    Generate states to be used for testing, using the given fluents (each state will add a fluent)

    Arguments
    ---------
    num_states : int
        The number of states to generate.

    Returns
    -------
    states : List of States
        The list of testing states generated.
    """
    states = []
    fluents = list(generate_test_fluents(num_states).items())
    for i in range(num_states):
        next_fluents = dict(fluents[: i + 1])
        state = State(next_fluents)
        states.append(state)
    return states


def generate_test_steps(num_steps: int):
    """
    Generate steps to be used for testing, given the number of steps and possible actions and states.

    Arguments
    ---------
    num_steps : int
        The number of steps to generate.

    Returns
    -------
    steps : List of Steps
        The list of testing steps generated.
    """
    steps = []
    actions = generate_test_actions(num_steps - 1)
    actions.append(None)
    states = generate_test_states(num_steps)
    for i in range(num_steps):
        step = Step(states[i], actions[i], i)
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
    trace = Trace(generate_test_steps(complexity))
    return trace


def generate_test_trace_list(length: int):
    from random import randint

    traces = []
    for _ in range(length):
        comp = randint(1, 3)
        trace = generate_test_trace(comp)
        traces.append(trace)
    return TraceList(traces)


def generate_observer_model():
    traces = generate_test_trace_list(2)
    observations = traces.tokenize(IdentityObservation)
    model = Extract(observations, modes.OBSERVER)
    return model
