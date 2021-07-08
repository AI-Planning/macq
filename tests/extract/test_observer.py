import pytest
from macq.extract import Extract, modes
from macq.observation import *
from macq.trace import *
from tests.utils.test_traces import blocks_world


def test_observer():
    traces = blocks_world(5)
    observations = traces.tokenize(IdentityObservation)
    model = Extract(observations, modes.OBSERVER)
    assert model

    with pytest.raises(InvalidQueryParameter):
        observations.fetch_observations({"test": "test"})


if __name__ == "__main__":
    traces = blocks_world(5)
    observations = traces.tokenize(IdentityObservation)
    traces.print()
    model = Extract(observations, modes.OBSERVER)
    print(model.details())
