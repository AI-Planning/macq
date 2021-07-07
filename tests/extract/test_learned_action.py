import json
from macq.extract import *


def test_learned_action():
    action1_json = json.loads(
        '{"name":"action1", "obj_params":["A", "B"], "cost":0, "precond":"C", "add":"B", "delete":"A"}'
    )
    action2_json = json.loads(
        '{"name":"action2", "obj_params":["A", "B"], "cost":0, "precond":["C","B"], "add":["B","D"], "delete":"A"}'
    )

    action1 = LearnedAction._deserialize(action1_json)
    assert action1

    action2 = LearnedAction._deserialize(action2_json)

    assert action1.compare(action2) == ({"B"}, {"D"}, set())

    assert action1 == action1
    assert action1 != action2
    assert action1 != action1_json
