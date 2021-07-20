from logging import warn
from typing import List, Callable, Type, Optional
from rich.console import Console
from . import Action, Trace
from ..observation import Observation
import macq.trace as TraceAPI


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

    # Allow child classes to have traces as a list of any type
    traces: List

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
        traces: List[Trace] = None,
        generator: Optional[Callable] = None,
    ):
        """Initializes a TraceList with a list of traces and a generator.

        Args:
            traces (list):
                Optional; The list of `Trace` objects.
            generator (function):
                Optional; The function used to generate the traces.
        """
        self.traces = [] if traces is None else traces
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

    def __contains__(self, item):
        return item in self.traces

    def append(self, item):
        self.traces.append(item)

    def clear(self):
        self.traces.clear()

    def copy(self):
        return self.traces.copy()

    def extend(self, iterable):
        self.traces.extend(iterable)

    def index(self, value):
        return self.traces.index(value)

    def insert(self, index: int, item):
        self.traces.insert(index, item)

    def pop(self):
        return self.traces.pop()

    def remove(self, value):
        self.traces.remove(value)

    def reverse(self):
        self.traces.reverse()

    def sort(self, reverse: bool = False, key: Callable = lambda e: e.get_total_cost()):
        self.traces.sort(reverse=reverse, key=key)

    def print(self, view="details", filter_func=lambda _: True, wrap=None):
        """Pretty prints the trace list in the specified view.

        Arguments:
            view ("details" | "color"):
                Specifies the view format to print in. "details" provides a
                detailed summary of each step in a trace. "color" provides a
                color grid, mapping fluents in a step to either red or green
                corresponding to the truth value.
        """
        console = Console()

        views = ["details", "color"]
        if view not in views:
            warn(f'Invalid view {view}. Defaulting to "details".')
            view = "details"

        traces = []
        if view == "details":
            if wrap is None:
                wrap = False
            traces = [trace.details(wrap=wrap) for trace in self]

        elif view == "color":
            if wrap is None:
                wrap = True
            traces = [
                trace.colorgrid(filter_func=filter_func, wrap=wrap) for trace in self
            ]

        for trace in traces:
            console.print(trace)
            print()

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

        self.traces.extend([self.generator() for _ in range(num)])

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

    def get_fluents(self):
        """Retrieves a set of all fluents used in child traces.

        Returns:
            A set of all fluents used in child traces.
        """
        fluents = set()
        for trace in self.traces:
            for step in trace:
                fluents.update(step.state.fluents)
        return fluents

    def tokenize(self, Token: Type[Observation], **kwargs):
        """Tokenizes the steps in this trace.

        Args:
            Token (Observation):
                A subclass of `Observation`, defining the method of tokenization
                for the steps.
        """
        return TraceAPI.ObservationLists(self, Token, **kwargs)
