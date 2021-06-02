from typing import Type
from . import TraceList
from ..observation import Observation


class ObservationList(TraceList):
    def __init__(self, traces: TraceList, Token: Type[Observation], **kwargs):
        self.type = Token
        self.traces = []
        for trace in traces:
            observations = trace.tokenize(Token, **kwargs)
            self.traces.append(observations)
