from macq.trace import *


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
    next_fluents = []
    fluents = generate_test_fluents(num_states)
    for i in range(num_states):
        state_name = "state " + str(i + 1)
        next_fluents = fluents[: i + 1]
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
    actions = generate_test_actions(num_steps)
    states = generate_test_states(num_steps)
    for i in range(num_steps):
        step = Step(actions[i], states[i])
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
