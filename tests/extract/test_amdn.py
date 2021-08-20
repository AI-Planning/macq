from macq.trace.disordered_parallel_actions_observation_lists import (
    default_theta_vec,
    num_parameters_feature,
    objects_shared_feature,
)
from macq.utils.tokenization_errors import TokenizationError
from tests.utils.generators import generate_blocks_traces
from macq.extract import Extract, modes
from macq.generate.pddl import RandomGoalSampling
from macq.observation import *
from macq.trace import *

from pathlib import Path
import pytest


def test_tokenization_error():
    with pytest.raises(TokenizationError):
        trace = generate_blocks_traces(3)[0]
        trace.tokenize(Token=NoisyPartialDisorderedParallelObservation)


def test_observations():
    base = Path(__file__).parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    # TODO: replace with a domain-specific random trace generator
    traces = RandomGoalSampling(
        prob=prob,
        dom=dom,
        # problem_id=2337,
        observe_pres_effs=True,
        num_traces=1,
        steps_deep=10,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=True,
    ).traces

    features = [objects_shared_feature, num_parameters_feature]
    learned_theta = default_theta_vec(2)
    observations = traces.tokenize(
        Token=NoisyPartialDisorderedParallelObservation,
        ObsLists=DisorderedParallelActionsObservationLists,
        features=features,
        learned_theta=learned_theta,
        percent_missing=0.10,
        percent_noisy=0.05,
    )

    assert observations.traces


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    # TODO: replace with a domain-specific random trace generator
    traces = RandomGoalSampling(
        prob=prob,
        dom=dom,
        # problem_id=2337,
        observe_pres_effs=True,
        num_traces=1,
        steps_deep=10,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=True,
    ).traces

    features = [objects_shared_feature, num_parameters_feature]
    learned_theta = default_theta_vec(2)
    observations = traces.tokenize(
        Token=NoisyPartialDisorderedParallelObservation,
        ObsLists=DisorderedParallelActionsObservationLists,
        features=features,
        learned_theta=learned_theta,
        percent_missing=0.10,
        percent_noisy=0.05,
    )
