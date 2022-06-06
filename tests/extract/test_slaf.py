import pytest
from pathlib import Path
from macq.extract import Extract, modes
from macq.observation import *
from macq.trace import *
from tests.utils.generators import generate_blocks_traces


def test_slaf():
    traces = generate_blocks_traces(plan_len=2, num_traces=1)
    observations = traces.tokenize(
        AtomicPartialObservation,
        percent_missing=0.10,
    )
    model = Extract(observations, modes.SLAF)
    assert model

    with pytest.raises(InvalidQueryParameter):
        observations.fetch_observations({"test": "test"})


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    model_blocks_dom = str(
        (base / "pddl_testing_files/model_blocks_domain.pddl").resolve()
    )
    model_blocks_prob = str(
        (base / "pddl_testing_files/model_blocks_problem.pddl").resolve()
    )

    traces = generate_blocks_traces(plan_len=2, num_traces=1)
    observations = traces.tokenize(
        AtomicPartialObservation,
        percent_missing=0.10,
    )
    traces.print()
    model = Extract(observations, modes.SLAF)
    print(model.details())

    model.to_pddl(
        "model_blocks_dom", "model_blocks_prob", model_blocks_dom, model_blocks_prob
    )
