from typing import Iterable, List, Callable
from . import Action
from . import Trace


class TraceList:
    """A collection of traces.

    A `list`-like object, where each element is a `Trace` of the same planning
    problem.


    Attributes:
        traces (list):
            The list of `Trace` objects.
        generator (function | None):
            The function used to generate the traces.
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
        traces: List[Trace] = [],
        generator: Callable = None,
    ):
        """Initializes a TraceList with a list of traces and a generator.

        Args:
            traces (list):
                Optional; The list of `Trace` objects.
            generator (function):
                Optional; The function used to generate the traces.
        """
        self.traces: List[Trace] = traces
        self.generator = generator

    def __str__(self):
        string = "TraceList:\n"
        for trace in self:
            for line in str(trace).splitlines():
                string += f"    {line}\n"
        return string


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
        """Generates more traces using the generator function.

        Args:
            num (int):
                The number of additional traces to generate.

        Raises:
            MissingGenerator: Cannot generate more traces if the generator
            function is not provided.
        """
        if self.generator is None:
            raise self.MissingGenerator(self)

        self.traces.extend(self.generator(num))

    def get_usage(self, action: Action):
        """Calculates how often an action was performed in each of the traces.

        Args:
            action (Action):
                The action to find the usage of.

        Returns:
            The frequency of the action in each of the traces. A percentage,
            calculated as the number of occurences of the action divided by the
            length of the trace (number of steps).
        """
        usages = []
        for trace in self:
            usages.append(trace.get_usage(action))
        return usages
