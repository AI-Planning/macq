from enum import Enum, auto
from .model import Model
from ..trace import TraceList


class modes(Enum):
    """Model extraction techniques."""

    OBSERVER = auto()


class Extract:
    """
    The Extract class uses the provided extraction method to return a Model
    object on instantiation.
    """

    def __new__(cls, traces: TraceList, mode: modes):
        """
        Extracts a Model object from `traces` using the specified extraction
        technique.

        Arguments
        ---------
        traces : TraceList
            The trace list to extract a model from.
        mode : Enum
            The extraction technique to use.

        Returns
        -------
        A Model object : Model
        """
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
