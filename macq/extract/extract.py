from enum import Enum, auto
from .model import Model
from ..trace import TraceList


class modes(Enum):
    OBSERVER = auto()


class Extract:
    def __new__(cls, traces: TraceList, mode: modes):
        if mode == modes.OBSERVER:
            return Extract._extract_observer(traces)

    @staticmethod
    def _get_fluents(traces: TraceList):
        fluents = set()
        for trace in traces:
            for fluent in trace.fluents:
                fluents.add(fluent)
        return list(fluents)

    @staticmethod
    def _get_actions(traces: TraceList):
        actions = set()
        for trace in traces:
            for action in trace.actions:
                actions.add(action)
        return list(actions)

    @staticmethod
    def _extract_observer(traces: TraceList):
        fluents = Extract._get_fluents(traces)
        actions = Extract._get_actions(traces)
        return Model(fluents, actions)
