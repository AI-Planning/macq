from macq.extract import Extract, modes
from macq.observation import (
    PartialObservabilityTokenPropositions,
    PartialObservabilityToken,
)
from macq.trace import *
from tests.utils.realistic_trace import real_trace_list


if __name__ == "__main__":
    traces = real_trace_list()
    observations = traces.tokenize(
        PartialObservabilityTokenPropositions,
        method=PartialObservabilityToken.random_subset,
        percent_missing=30,
    )
    traces.print()
    model = Extract(observations, modes.SLAF)
    print(model.details())
