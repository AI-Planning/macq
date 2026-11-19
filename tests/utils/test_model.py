from tests.utils.test_traces import blocks_world
from macq.observation import *
import macq.extract as extract


def extract_observer(traces):
    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    return model


def generate_test_model():
    traces = blocks_world(10)
    return extract_observer(traces)
