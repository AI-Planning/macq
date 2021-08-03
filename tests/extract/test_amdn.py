import pytest
from macq.extract import Extract, modes
from macq.observation import *
from macq.trace import *
from tests.utils.generators import generate_blocks_traces

if __name__ == "__main__":
    # TODO: use goal sampling traces here instead for now. will eventually be replaced by a domain-specific random trace generator
    traces = generate_blocks_traces(plan_len=3, num_traces=1)
    observations = traces.tokenize(
        NoisyPartialObservation,
        percent_missing=0.10,
        percent_noisy=0.05,
    )
    #model = Extract(observations, modes.SLAF, debug_mode=True)
    #print(model.details())