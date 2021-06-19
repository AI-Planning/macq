from tests.utils.generators import generate_test_fluents


def test_compare():
    fluent1 = generate_test_fluents(3)
    fluent2 = generate_test_fluents(3)
    assert fluent1 == fluent2
