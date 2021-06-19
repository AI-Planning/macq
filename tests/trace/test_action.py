from tests.utils.generators import generate_test_actions


def test_compare():
    action1 = generate_test_actions(3)[0]
    action2 = generate_test_actions(3)[0]
    assert action1 == action2
