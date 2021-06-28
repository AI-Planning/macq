from macq import extract
from macq.observation import IdentityObservation


def extract_model(traces):
    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    return model
