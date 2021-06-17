import pytest
from macq import generate, extract
from macq.observation import IdentityObservation


def generate_traces():
    traces = generate.pddl.VanillaSampling(
        problem_id=123, plan_len=20, num_traces=1
    ).traces

    # traces.generate_more(10)

    return traces


def test_readme():
    traces = generate_traces()
    assert len(traces) == 1

    action = traces[0][0].action
    traces.get_usage(action)

    trace = traces[0]
    trace.fluents
    trace.actions
    trace.get_pre_states(action)
    trace.get_post_states(action)
    trace.get_total_cost()

    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    model.details()


if __name__ == "__main__":
    test_readme()
