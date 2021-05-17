#import macq
from macq.trace import CustomObject, Fluent, Action, Step, State, Trace
from macq.observation import IdentityObservation

InvalidCostRange = Trace.InvalidCostRange
InvalidFluent = Action.InvalidFluent

from typing import List
import pytest


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
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)

    action.add_precond([fluent1])
    assert action.precond == [fluent1]
    action.add_precond([fluent2, fluent3])
    assert action.precond == [fluent1, fluent2, fluent3]

# ensure that valid fluents can be added as action effects
def test_action_add_effects():
    objects = [CustomObject("number", str(o)) for o in range(6)]
    action = Action("put down", objects, [], [], [], 1)
    fluent1 = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    fluent4 = Fluent("picked up", [objects[3]], True)
    fluent5 = Fluent("on top", [objects[4]], False)
    fluent6 = Fluent("red", [objects[5]], False)

    action.add_effect_add([fluent4])
    assert action.add == [fluent4]
    action.add_effect_add([fluent5, fluent6])
    assert action.add == [fluent4, fluent5, fluent6]
    action.add_effect_delete([fluent1])
    assert action.delete == [fluent1]
    action.add_effect_delete([fluent2, fluent3])
    assert action.delete == [fluent1, fluent2, fluent3]

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
