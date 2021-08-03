import pytest
from macq.extract import Extract, modes
from macq.observation import *
from macq.trace import *
from tests.utils.generators import generate_blocks_traces

if __name__ == "__main__":
    traces = generate_blocks_traces(plan_len=3, num_traces=1)
    observations = traces.tokenize(
        NoisyPartialObservation,
        percent_missing=1,
        percent_noisy=0.05,
        replace_noisy=True
    )
    #model = Extract(observations, modes.SLAF, debug_mode=True)
    #print(model.details())