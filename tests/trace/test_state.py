from tests.utils.generators import generate_test_states, generate_test_fluents


def test_state():
    s1, s2, s3 = generate_test_states(3)

    assert s1.details()
    assert str(s1)
    assert s1 != s2
    assert s1 == s1
    assert s1 != "test"
    assert len(s1) == 1

    fluent = generate_test_fluents(1)[0]
    s1[fluent] = False
    assert not s1[fluent]


if __name__ == "__main__":
    test_state()
