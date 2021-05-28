from enum import Enum, auto
from .observer import Observer
from ..trace import TraceList


class modes(Enum):
    """Model extraction techniques.

    An Enum where each value represents a model extraction technique.
    """

    OBSERVER = auto()


class Extract:
    """Extract models from traces.

    The Extract class uses an extraction method to retrieve an action Model
    from state traces.
    """

    def __new__(cls, traces: TraceList, mode: modes):
        """Extracts a Model object.

        Extracts a model from the traces using the specified extraction
        technique.

        Args:
            traces (TraceList): The state traces to extract the model from.
            mode (Enum): The extraction technique to use.

        Returns:
            A Model object. The model's characteristics are determined by the
            extraction technique used.
        """
        if mode == modes.OBSERVER:
            return Observer(traces)
