import pytest
from tests.test_core import generate_test_trace_list
from macq.extract import Extract, modes


def generate_observer_model():
    traces = generate_test_trace_list(2)
    model = Extract(traces, modes.OBSERVER)
    return model
