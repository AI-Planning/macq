import pytest
from pathlib import Path
from macq import generate, extract
from macq.observation import IdentityObservation


def generate_traces():
    # traces = generate.pddl.VanillaSampling(
    #     problem_id=15, plan_len=20, num_traces=1
    # ).traces
    base = Path(__file__).parent.parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    traces = generate.pddl.VanillaSampling(
        dom=dom, prob=prob, plan_len=5, num_traces=5  # type: ignore
    ).traces  # traces.generate_more(1)
    print(traces[0][2].state.details())

    return traces


def test_readme():
    traces = generate_traces()
    assert len(traces) == 5

    action1 = traces[0][0].action
    action1_usage = traces.get_usage(action1)
    # assert action1_usage == [0.05] * len(traces)

    trace = traces[0]
    # assert len(trace) == 20

    trace.fluents
    trace.actions
    trace.get_pre_states(action1)
    trace.get_post_states(action1)

    cost = trace.get_total_cost()
    assert cost == 0

    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    model.details()
    print(model.details())


if __name__ == "__main__":
    test_readme()
