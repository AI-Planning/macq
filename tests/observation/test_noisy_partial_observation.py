from macq.observation import NoisyPartialDisorderedParallelObservation
from tests.utils.generators import generate_blocks_traces

if __name__ == "main":
    traces = generate_blocks_traces(5)
    obs_lists = traces.tokenize(NoisyPartialDisorderedParallelObservation)