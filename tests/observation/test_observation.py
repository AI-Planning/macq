import pytest
from macq.observation import *


def test_observation():
    o = Observation(index=1)
    with pytest.raises(NotImplementedError):
        o.matches({"test": "test"})

    assert o.serialize()
