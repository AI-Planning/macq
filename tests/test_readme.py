from macq import generate, extract
from macq.observation import IdentityObservation


def generate_traces():
    traces = generate.pddl.VanillaSampling(
        problem_id=2336, plan_len=5, num_traces=3, seed=42
    ).traces
    traces.generate_more(1)

    return traces


def extract_model(traces):
    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    return model


def test_readme():
    traces = generate_traces()
    assert len(traces) == 4

    action1 = traces[0][0].action
    assert action1
    assert traces.get_usage(action1)

    trace = traces[0]
    assert len(trace) == 5

    trace.fluents
    trace.actions
    trace.get_pre_states(action1)
    trace.get_post_states(action1)

    cost = trace.get_total_cost()
    assert cost == 0

    model = extract_model(traces)
    model.details()  # in the readme, so worth having to guaruntee no errors


if __name__ == "__main__":
    # run as a script to look over the extracted model
    traces = generate_traces()
    model = extract_model(traces)
    print(model.details())
