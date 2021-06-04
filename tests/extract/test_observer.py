from macq.extract import Extract, modes
from macq.trace import *
from tests.realistic_trace import real_trace_list


if __name__ == "__main__":
    traces = real_trace_list()
    print(traces)
    model = Extract(traces, modes.OBSERVER)
    print(str(model))
