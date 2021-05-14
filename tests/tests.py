from macq.trace import CustomObject, Fluent, Action, Step, State, Trace

if __name__ == "__main__":
    objects = [CustomObject("number", str(o)) for o in range(6)]
    other_object = CustomObject("other", 10)

    fluent = Fluent("on table", [objects[0]], True)
    fluent2 = Fluent("in hand", [objects[1]], True)
    fluent3 = Fluent("dropped", [objects[2]], False)
    fluent4 = Fluent("picked up", [objects[3]], True)
    fluent5 = Fluent("on top", [objects[4]], False)
    other = Fluent("put down other", [other_object], True)

    precond = [fluent, fluent2]
    add = [fluent3, fluent4]
    delete = [fluent]

    action = Action("put down", objects, precond, add, delete, 1)
    action2 = Action("pick up", objects, precond, add, delete, 3)
    action3 = Action("restart", objects, precond, add, delete, 5)

    print(action.precond)
    # should crash
    # action.add_precond([other])
    # print(action.precond)
    action.add_precond([fluent5])
    print(action.precond)
    print()

    print(action.add)
    # should crash
    # action.add_effect_add([other])
    # print(action.add)
    action.add_effect_add([fluent5])
    print(action.add)
    print()

    print(action.delete)
    # should crash
    # action.add_effect_delete([other])
    # print(action.delete)
    action.add_effect_delete([fluent5])
    print(action.delete)
    print()

    print(action.obj_params)
    action.add_parameter(other_object)
    print(action.obj_params)

    # should crash
    # print(action.__add_fluent([other], action.precond))

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
    print(trace.get_cost_range(1, 3))
    print(trace.get_cost_range(1, 2))
    print(trace.get_cost_range(2, 3))

    # error testing
    # print(trace.get_cost_range(3,1))
    # print(trace.get_cost_range(0,2))
    # print(trace.get_cost_range(1,5))

    print(trace.get_usage(action))

    print(trace.get_sas_triples(action3))
