from enum import Enum, auto
from .observer import Observer
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
            return Observer(traces)
