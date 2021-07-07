import pytest
from pathlib import Path
from macq.generate.pddl import VanillaSampling
from macq.generate import InvalidNumberOfTraces, InvalidPlanLength


def test_invalid_vanilla_sampling():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/playlist_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/playlist_problem.pddl").resolve())

    with pytest.raises(InvalidPlanLength):
        VanillaSampling(dom=dom, prob=prob, plan_len=-1, num_traces=5)

    with pytest.raises(InvalidNumberOfTraces):
        VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=-1)
