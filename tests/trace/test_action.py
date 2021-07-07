from macq.trace import PlanningObject
from tests.utils.generators import generate_test_actions


def test_action():
    actions = generate_test_actions(2)
    a1 = actions[0]
    a2 = actions[1]

    assert a1 == a1.clone()
    assert a1 != a2

    assert str(a1)

    obj = PlanningObject("test_obj", "test")
    a1.add_parameter(obj)
    assert obj in a1.obj_params
