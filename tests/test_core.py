#import macq
from macq.trace import CustomObject, Fluent, Action, Step, State, Trace
from macq.observation import IdentityObservation

InvalidCostRange = Trace.InvalidCostRange
InvalidFluent = Action.InvalidFluent

from typing import List
import pytest

# HELPER FUNCTIONS

# generates basic fluents to be used for testing
def generate_test_fluents(num_fluents):
    fluents = []
    objects = [CustomObject("number", str(o)) for o in range(num_fluents)]
    for i in range(num_fluents):
        fluent_name = "fluent" + " " + str(i)
        if i % 2 == 0:
            value = True
        else:
            value = False
        fluent = Fluent(fluent_name, [objects[i]], value)
        fluents.append(fluent)
    return fluents

# generates basic actions to be used for testing
def generate_test_actions(num_actions, objects):
    actions = []
    for i in range(num_actions):
        action_name = "action" + " " + str(i)
        action = Action(action_name, objects, [], [], [], i)
        actions.append(action)
    return actions

# returns the objects used by the given fluents in a list
def get_fluent_obj(fluents):
    objects = []
    for fluent in fluents:
        for obj in fluent.objects:
            objects.append(obj)
    return objects

# generate states to be used for testing, using the given fluents (each state will add a fluent)
def generate_test_states(num_states, fluents):
    states = []
    next_fluents = []
    for i in range(num_states):
        state_name = "state" + " " + str(i)
        if i < len(fluents):
            next_fluents.append(fluents[i])
        state = State(next_fluents)
        states.append(state)
    return states

# generate steps to be used for testing, given the number of steps and possible actions and states
def generate_test_steps(num_steps, actions, states):
    steps = []
    # indices for actions and states respectively
    a_index = 0
    s_index = 0
    for i in range(num_steps):
        # cycle through actions and states
        if a_index < len(actions):
            a_index += 1
        else:
            a_index = 0
        if s_index < len(states):
            s_index += 1
        else:
            s_index = 0
        step = Step(actions[a_index], states[s_index])
        steps.append(step)
    return steps

# generate a test trace with the given complexity (number of actions, fluents, states, and steps)
def generate_test_trace(complexity):
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

# test the functionality to add steps to a trace
def test_trace_add_steps():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    step4 = Step(action1, state3)
    trace = Trace([step1, step2, step3])

    trace.add_steps([step4])
    assert trace.steps == [step1, step2, step3, step4]

# ensure that the Trace base_fluents() and base_actions() functions work correctly
def test_trace_base():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.base_fluents() == ["on table", "in hand", "dropped"]
    assert trace.base_actions() == ["put down", "pick up", "restart"]

# test that the previous states are being retrieved correctly
def test_trace_prev_states():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.get_prev_states(action1) == [state1]
    assert trace.get_prev_states(action3) == [state3]

# test that the post states are being retrieved correctly
def test_trace_post_states():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.get_post_states(action1) == [state2]
    assert trace.get_post_states(action3) == []

# test trace SAS triples function
def test_trace_get_sas_triples():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.get_sas_triples(action2) == [(state2, action2, state3)]
    assert trace.get_sas_triples(action3) == [(state3, action3)]

# test that the total cost is working correctly
def test_trace_total_cost():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.get_total_cost() == 9

# test that the cost range is working correctly
def test_trace_valid_cost_range():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.get_cost_range(1, 3) == 9
    assert trace.get_cost_range(1, 2) == 4
    assert trace.get_cost_range(2, 3) == 8

# test that incorrect provided cost ranges throw errors
def test_trace_invalid_cost_range():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    with pytest.raises(InvalidCostRange):
        trace.get_cost_range(3, 1)
        trace.get_cost_range(0, 2)
        trace.get_cost_range(1, 5)

# test trace action usage
def test_trace_usage():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    assert trace.get_usage(action1) == 1 / 3

# test trace tokenize function
def test_trace_tokenize():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action1 = Action("put down", objects, [], [], [], 1)
    action2 = Action("pick up", objects, [], [], [], 3)
    action3 = Action("restart", objects, [], [], [], 5)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    state1 = State([fluent1])
    state2 = State([fluent1, fluent2])
    state3 = State([fluent1, fluent2, fluent3])
    step1 = Step(action1, state1)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    trace = Trace([step1, step2, step3])
    trace.tokenize(IdentityObservation)
    print(trace.observations)
    print([
        IdentityObservation(step1),
        IdentityObservation(step2),
        IdentityObservation(step3),
    ])
    assert trace.observations == [
        IdentityObservation(step1),
        IdentityObservation(step2),
        IdentityObservation(step3),
    ]
    # test equality dunder by attempting to compare an object of a different type
    assert trace.observations != step1
