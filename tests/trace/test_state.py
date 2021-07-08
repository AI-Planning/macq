import pytest
from macq.trace import State
from tests.utils.generators import generate_test_states, generate_test_fluents


def test_state():
    s1, s2 = generate_test_states(2)

    assert s1.details()
    assert str(s1)
    assert s1 != s2
    assert s1 == State(s1.copy())
    assert s1 == s1.clone()
    assert s1 != "test"
    assert len(s1) == 1

    fluents = generate_test_fluents(3)
    fluent = fluents[0]
    assert s1.holds(fluent.name)
    s1[fluent] = False
    assert not s1[fluent]
    assert fluent not in s1

    del s1[fluent]
    with pytest.raises(KeyError):
        s1[fluent]

    for v in s1.values():
        assert isinstance(v, bool)

    s1.clear()
    s1.update(dict(zip(fluents, [i % 2 == 0 for i in range(3)])))
    for f in fluents:
        assert s1.has_key(f)
    for f in s1:
        assert f in fluents
