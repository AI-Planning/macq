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

    def __init__(
        self,
        traces: Union[List[Trace], None] = None,
        generator: Union[Callable, None] = None,
    ):
        """
        Creates a TraceList object. This stores a list of traces and optionally
        the function used to generate the traces.

        Attributes
        ----------
        traces : List
            The list of `Trace` objects.
        generator : funtion | None
            (Optional) The function used to generate the traces.
        """
        self.traces: List[Trace] = [] if traces is None else traces
        self.generator = generator

    def __len__(self):
        return len(self.traces)

    def __setitem__(self, key: int, value: Trace):
        self.traces[key] = value

    def __getitem__(self, key: int):
        return self.traces[key]

    def __delitem__(self, key: int):
        del self.traces[key]

    def __iter__(self):
        return iter(self.traces)

    def __reversed__(self):
        return reversed(self.traces)

    def __contains__(self, item: Trace):
        return item in self.traces

    def append(self, item: Trace):
        self.traces.append(item)

    def generate_more(self, num: int):
        if self.generator is None:
            raise self.MissingGenerator(self)

        self.traces.extend(self.generator(num))

    def get_usage(self, action: Action):
        usages = []
        for trace in self.traces:
            usages.append(trace.get_usage(action))
        return usages
