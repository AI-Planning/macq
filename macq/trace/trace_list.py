from typing import Iterable, Union, List, Callable
from . import Action
from . import Trace


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
        traces : list
            The list of `Trace` objects.
        generator : funtion | None
            (Optional) The function used to generate the traces.
        """
        self.traces: List[Trace] = [] if traces is None else traces
        self.generator = generator

    def __str__(self):
        string = "["
        for trace in self:
            string += "\n"
            string += "-" * 100
            string += "\n\n"
            string += str(trace)
        string += "]"
        return string

    def __repr__(self):
        rep = "["
        for trace in self:
            rep += "\n"
            rep += "-" * 100
            rep += "\n\n"
            rep += repr(trace)
        rep += "]"
        return rep


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

    def clear(self):
        self.traces.clear()

    def copy(self):
        return self.traces.copy()

    def count(self, value: Trace):
        return self.traces.count(value)

    def extend(self, iterable: Iterable[Trace]):
        self.traces.extend(iterable)

    def index(self, value: Trace):
        return self.traces.index(value)

    def insert(self, index: int, item: Trace):
        self.traces.insert(index, item)

    def pop(self):
        return self.traces.pop()

    def remove(self, value: Trace):
        self.traces.remove(value)

    def reverse(self):
        self.traces.reverse()

    def sort(self, reverse: bool = False, key: Callable = lambda e: e.get_cost()):
        self.traces.sort(reverse=reverse, key=key)

    def generate_more(self, num: int):
        if self.generator is None:
            raise self.MissingGenerator(self)

        self.traces.extend(self.generator(num))

    def get_usage(self, action: Action):
        usages = []
        for trace in self:
            usages.append(trace.get_usage(action))
        return usages
