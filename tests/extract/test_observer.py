from macq.extract import Extract, modes
from macq.observation import IdentityObservation
from macq.trace import *
from tests.utils.realistic_trace import real_trace_list


if __name__ == "__main__":
    traces = real_trace_list()
    observations = traces.tokenize(IdentityObservation)
    print(traces)
    model = Extract(observations, modes.OBSERVER)
    print(str(model))
