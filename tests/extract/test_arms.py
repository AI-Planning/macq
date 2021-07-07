from macq.extract import Extract, modes
from macq.observation import PartialObservation
from tests.utils.generators import generate_blocks_traces


if __name__ == "__main__":
    traces = generate_blocks_traces(plan_len=10, num_traces=100)  # need a goal
    observations = traces.tokenize(
        PartialObservation,
        method="random",
        percent_missing=0.10,
    )
    model = Extract(observations, modes.ARMS)
    print()
    print(model.details())
