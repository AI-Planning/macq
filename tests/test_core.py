import macq
from macq.trace.Fluent import CustomObject, Fluent
from macq.trace.Action import Action, InvalidFluentException
from macq.trace.State import State
from macq.trace.Step import Step
from macq.trace.Trace import Trace
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
action = Action("put down", objects, precond, add, delete, 1)
action2 = Action("pick up", objects, precond, add, delete, 3)   
action3 = Action("restart", objects, precond, add, delete, 5)
# create fluents
fluent = Fluent("on table", [objects[0]], True)
fluent2 = Fluent("in hand", [objects[1]], True)
fluent3 = Fluent("dropped", [objects[2]], False)
fluent4 = Fluent("picked up", [objects[3]], True)
fluent5 = Fluent("on top", [objects[4]], False)
other = Fluent("put down other", [other], True)
# create test states
state = State([fluent])
state2 = State([fluent, fluent2])
state3 = State([fluent, fluent2, fluent3])
# create test steps
step = Step(action, state)
step2 = Step(action2, state2)
step3 = Step(action3, state3)
# create test trace
trace = Trace([step, step2, step3])

# ensure that invalid fluents can't be added to actions
def test_action_errors():
    with pytest.raises(InvalidFluentException):
        action.add_effect_add([other])
        action.add_precond([other])
        action.add_effect_delete([other])
# ensure that valid fluents can be added as action conditions correctly
def test_action_add_conditions():
    action.add_precond([fluent5])
    assert action.precond == [fluent5]

if __name__ == "__main__":
    action.add_effect_add([fluent5])
    print(action.add)
    print()

    action.add_effect_delete([fluent5])
    print(action.delete)
    print()

    print(action.obj_params)
    action.add_parameter(other)
    print(action.obj_params)

    #should crash
    #print(action.__add_fluent([other], action.precond))

    print("test step")
    print(step.base_action())
    print(step.base_fluents())
    
    print(trace.steps)
    print(trace.num_fluents)
    print(trace.fluents)
    print(trace.actions)
    print(trace.get_prev_states(action2))
    print(trace.get_post_states(action2))
    print(trace.get_total_cost())
    print(trace.get_cost_range(1,3))
    print(trace.get_cost_range(1,2))
    print(trace.get_cost_range(2,3))

    #error testing
    #print(trace.get_cost_range(3,1))
    #print(trace.get_cost_range(0,2))
    #print(trace.get_cost_range(1,5))

    print(trace.get_usage(action))

    print(trace.get_sas_triples(action3))
   