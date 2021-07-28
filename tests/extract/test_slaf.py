import pytest
from macq.extract import Extract, modes
from macq.observation import *
from macq.trace import *
from tests.utils.generators import generate_blocks_traces


def test_slaf():
    traces = generate_blocks_traces(plan_len=2, num_traces=1)
    observations = traces.tokenize(
        AtomicPartialObservation,
        method=AtomicPartialObservation.random_subset,
        percent_missing=0.10,
    )
    model = Extract(observations, modes.SLAF)
    assert model

    with pytest.raises(InvalidQueryParameter):
        observations.fetch_observations({"test": "test"})


if __name__ == "__main__":
    traces = generate_blocks_traces(plan_len=3, num_traces=1)
    observations = traces.tokenize(
        AtomicPartialObservation,
        method=AtomicPartialObservation.random_subset,
        percent_missing=0.10,
    )
    traces.print()
    model = Extract(observations, modes.SLAF, debug_mode=True)
    print(model.details())
