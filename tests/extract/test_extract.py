import pytest
from macq.extract import IncompatibleObservationToken, Extract, modes
from macq.observation import Observation
from tests.utils.realistic_trace import real_trace_list

# Other functionality of extract is implicitly tested by any extraction technique
# This is reflected in coverage reports


def test_incompatible_observation_token():
    traces = real_trace_list()
    observations = traces.tokenize(Observation)
    with pytest.raises(IncompatibleObservationToken):
        Extract(observations, modes.OBSERVER)
