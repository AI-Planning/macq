import pytest
from macq.extract import IncompatibleObservationToken, Extract, modes
from macq.observation import Observation
from tests.utils.test_traces import blocks_world

# Other functionality of extract is tested by extraction technique tests


def test_incompatible_observation_token():
    traces = blocks_world(1)
    observations = traces.tokenize(Observation)
    with pytest.raises(IncompatibleObservationToken):
        Extract(observations, modes.OBSERVER)
