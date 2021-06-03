from typing import Type, List
from . import TraceList
from ..observation import Observation


class ObservationList(TraceList):
    traces: List[Observation]
    # Disable methods
    generate_more = property()
    get_usage = property()
    tokenize = property()

    def __init__(
        self, traces: TraceList = None, Token: Type[Observation] = None, **kwargs
    ):
        self.type = Token
        self.traces = []
        for trace in traces:
            observations = trace.tokenize(Token, **kwargs)
            self.append(observations)
