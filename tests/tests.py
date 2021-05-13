import macq
from macq.trace.Fluent import CustomObject 

if __name__ == "__main__":
    objects = [CustomObject(str(o)) for o in range(3)]
    action = Action("put down", objects, 1)
    action2 = Action("pick up", objects, 3)
    action3 = Action("restart", objects, 5)
    # action.add_effect("eff", ["block 1", "block 2"], "func1", 94)
    # action.add_precond("precond", ["block 1", "block 2"])
    # action.add_effect("eff", ["block 1", "block 3"], "func1", 94)
    fluent = Fluent("on table", objects, True)
    fluent2 = Fluent("in hand", objects, True)
    fluent3 = Fluent("dropped", objects, False)

    state = State([fluent])
    state2 = State([fluent, fluent2])
    state3 = State([fluent, fluent2, fluent3])

    step = Step(action, state)
    step2 = Step(action2, state2)
    step3 = Step(action3, state3)
    
    trace = Trace([step, step2, step3])
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