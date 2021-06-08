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
