from macq.trace import CustomObject, Fluent, Action, Step, State, Trace
from macq.observation import IdentityObservation
CostRangeError = Trace.CostRangeError
InvalidFluentException = Action.InvalidFluentException

from typing import List
import pytest


# create objects 
objects = [CustomObject("number", str(o)) for o in range(6)]
other = CustomObject("other", 10)
# create a precondition and effect to test actions
precond = []
add = []
delete = []
# create test actions
action1 = Action("put down", objects, precond, add, delete, 1)
action2 = Action("pick up", objects, precond, add, delete, 3)   
action3 = Action("restart", objects, precond, add, delete, 5)
# create fluents
fluent1 = Fluent("on table", [objects[0]], True)
fluent2 = Fluent("in hand", [objects[1]], True)
fluent3 = Fluent("dropped", [objects[2]], False)
fluent4 = Fluent("picked up", [objects[3]], True)
fluent5 = Fluent("on top", [objects[4]], False)
fluent6 = Fluent("red", [objects[5]], False)
other = Fluent("put down other", [other], True)
# create test states
state1 = State([fluent1])
state2 = State([fluent1, fluent2])
state3 = State([fluent1, fluent2, fluent3])
# create test steps
step1 = Step(action1, state1)
step2 = Step(action2, state2)
step3 = Step(action3, state3)
step4 = Step(action1, state3)
# create test trace
trace = Trace([step1, step2, step3])

# TESTS FOR ACTION CLASS

# ensure that invalid fluents can't be added to actions
def test_action_errors():
    with pytest.raises(InvalidFluentException):
        action1.add_precond([other])
        action1.add_effect_add([other])
        action1.add_effect_delete([other])
# ensure that valid fluents can be added as action preconditions
def test_action_add_preconditions():
    action1.add_precond([fluent1])
    assert action1.precond == [fluent1]
    action1.add_precond([fluent2, fluent3])
    assert action1.precond == [fluent1, fluent2, fluent3]
# ensure that valid fluents can be added as action effects
def test_action_add_effects():
    action1.add_effect_add([fluent4])
    assert action1.add == [fluent4]
    action1.add_effect_add([fluent5, fluent6])
    assert action1.precond == [fluent4, fluent5, fluent6]
    action1.add_effect_delete([fluent1])
    assert action1.delete == [fluent1]
    action1.add_effect_delete([fluent2, fluent3])
    assert action1.delete == [fluent1, fluent2, fluent3]
# ensure that valid object parameters can be added and subsequently referenced
def test_action_add_params():
    action1.add_parameter(other)
    assert action1.obj_params == [objects, other]
    action1.add_precond([other])
    action1.add_effect_add([other])
    action1.add_effect_delete([other]) 
    assert action1.precond == [other]
    assert action1.add == [other]
    assert action1.delete == [other]

# TESTS FOR TRACE CLASS 

# test the functionality to add steps to a trace
def test_trace_add_steps():
    trace.add_steps(step4)
    assert trace.steps == [step1, step2, step3, step4]
# ensure that the Trace base_fluents() and base_actions() functions work correctly
def test_trace_base():
    assert trace.base_fluents() == ['on table', 'in hand', 'dropped']
    assert trace.base_actions() == ['put down', 'pick up', 'restart']
# test that the previous states are being retrieved correctly
def test_trace_prev_states():
    assert trace.get_prev_states(action1) == state1
    assert trace.get_prev_states(action3) == state3
# test that the post states are being retrieved correctly
def test_trace_post_states():
    assert trace.get_post_states(action1) == state2
    assert trace.get_post_states(action3) == []
# test trace SAS triples function
def test_trace_get_sas_triples():
    assert trace.get_sas_triples(action2) == (state2, action2, state3)
    assert trace.get_sas_triples(action3) == (state3, action3, [])
# test that the total cost is working correctly
def test_trace_total_cost():
    assert trace.get_total_cost() == 9
# test that the cost range is working correctly
def test_trace_valid_cost_range():
    assert trace.get_cost_range(1,3) == 9
    assert trace.get_cost_range(1,2) == 4
    assert trace.get_cost_range(2,3) == 8
# test that incorrect provided cost ranges throw errors
def test_trace_invalid_cost_range():
    with pytest.raises(CostRangeError):
        trace.get_cost_range(3,1)
        trace.get_cost_range(0,2)
        trace.get_cost_range(1,5)
# test trace action usage
def test_trace_usage():
    assert trace.get_usage(action1) == 1 / 3
# test trace tokenize function
def test_trace_tokenize():
    trace.tokenize(IdentityObservation())
    assert trace.observations == [IdentityObservation(step1), IdentityObservation(step2),
    IdentityObservation(step3)]
