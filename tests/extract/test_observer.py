import pytest
from pathlib import Path
from macq.extract import Extract, modes
from macq.observation import *
from macq.trace import *
from tests.utils.test_traces import blocks_world


def test_observer():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    model_blocks_dom = str(
        (base / "pddl_testing_files/model_blocks_domain.pddl").resolve()
    )
    model_blocks_prob = str(
        (base / "pddl_testing_files/model_blocks_problem.pddl").resolve()
    )

    traces = blocks_world(5)
    observations = traces.tokenize(IdentityObservation)
    model = Extract(observations, modes.OBSERVER)
    assert model
    model.to_pddl(
        "model_blocks_dom", "model_blocks_prob", model_blocks_dom, model_blocks_prob
    )
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

    traces = blocks_world(5)
    observations = traces.tokenize(IdentityObservation)
    traces.print()
    model = Extract(observations, modes.OBSERVER)
    print(model.details())
    model.to_pddl(
        "model_blocks_dom", "model_blocks_prob", model_blocks_dom, model_blocks_prob
    )
