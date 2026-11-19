import threading
from pathlib import Path

from macq.generate.pddl import RandomGoalSampling
from macq.trace import TraceList

BASE = Path(__file__).parent.parent.parent
DOM = str((BASE / "pddl_testing_files/blocks_domain.pddl").resolve())
PROB = str((BASE / "pddl_testing_files/blocks_problem.pddl").resolve())


def test_goal_search_stops_at_its_time_limit():
    threads = threading.active_count()
    sampler = RandomGoalSampling(
        dom=DOM,
        prob=PROB,
        num_traces=2,
        steps_deep=5,
        subset_size_perc=0.1,
        max_time=10,
    )
    assert isinstance(sampler.traces, TraceList)
    assert 1 <= len(sampler.traces) <= 2
    assert threading.active_count() == threads


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent

    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    random_sampler = RandomGoalSampling(
        dom=dom,
        prob=prob,
        steps_deep=20,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=False,
        max_time=10,
    )
    random_sampler.num_traces = 10
    random_sampler.generate_traces()
    traces = random_sampler.traces
    traces.print(wrap="y")

    # ensure traces are reassigned
    random_sampler.num_traces = 5
    random_sampler.generate_traces()
    traces = random_sampler.traces

    # test generating traces with action preconditions/effects known
    random_sampler_traces = RandomGoalSampling(
        dom=dom,
        prob=prob,
        observe_pres_effs=True,
        num_traces=3,
        steps_deep=10,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=False,
    ).traces
