from macq.extract import Extract, modes
from macq.observation import PartialObservabilityToken


from macq.generate.pddl import VanillaSampling
from tests.utils.generators import generate_blocks_traces


if __name__ == "__main__":
    traces = generate_blocks_traces(plan_len=3, num_traces=1)

    observations = traces.tokenize(
        PartialObservabilityToken,
        method=PartialObservabilityToken.random_subset,
        percent_missing=0.35,
    )
    model = Extract(observations, modes.SLAF)

    print()
    print(model.details())
