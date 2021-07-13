from macq.extract import Extract, modes
from macq.observation import AtomicPartialObservation
from tests.utils.generators import generate_blocks_traces

if __name__ == "__main__":
    traces = generate_blocks_traces(plan_len=3, num_traces=1)
    observations = traces.tokenize(
        AtomicPartialObservation,
        method=AtomicPartialObservation.random_subset,
        percent_missing=0.10,
    )
    traces.print()
    model = Extract(observations, modes.SLAF, debug_mode=False)
    print(model.details())
