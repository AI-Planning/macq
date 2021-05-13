from typing import Union, List, Callable
from .Action import Action
from .Trace import Trace


class TraceList:
    """
    A TraceList object is a list-like object that holds information about a
    series of traces.
    """

    class MissingGenerator(Exception):
        def __init__(
            self,
            trace_list,
            message="TraceList is missing a generate function.",
        ):
            self.trace_list = trace_list
            self.message = message
            super().__init__(message)

    def __init__(self, generator: Union[Callable, None] = None):
        """
        Creates a TraceList object. This stores a list of traces and optionally
        the function used to generate the traces.

        Attributes
        ----------
        traces : list
            The list of `Trace` objects.
        generator : funtion | None
            (Optional) The function used to generate the traces.
        """
        self.traces: List[Trace] = []
        self.generator = generator

    def generate_more(self, num: int):
        if self.generator is None:
            raise self.MissingGenerator(self)

        self.traces.extend(self.generator(num))

    def get_usage(self, action: Action):
        usages = []
        for trace in self.traces:
            usages.append(trace.get_usage(action))
        return usages
