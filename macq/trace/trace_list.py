from collections.abc import MutableSequence
from typing import Callable, List, Type, Union
from warnings import warn

from ..observation import Observation, ObservedTraceList
from . import Action, Trace


class TraceList(MutableSequence):
    """A sequence of traces.

    A `list`-like object, where each element is a `Trace` of the same planning
    problem.

    Attributes:
        traces (List[Trace]):
            The list of `Trace` objects.
        generator (Callable | None):
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

    traces: List[Trace]
    generator: Union[Callable, None]

    def __init__(
        self,
        traces: List[Trace] = None,
        generator: Callable = None,
    ):
        """Initializes a TraceList with a list of traces and a generator.

        Args:
            traces (List[Trace]):
                Optional; The list of `Trace` objects.
            generator (Callable):
                Optional; The function used to generate the traces.
        """
        self.traces = [] if traces is None else traces
        self.generator = generator

    def __getitem__(self, key: int):
        return self.traces[key]

    def __setitem__(self, key: int, value: Trace):
        self.traces[key] = value

    def __delitem__(self, key: int):
        del self.traces[key]

    def __iter__(self):
        return iter(self.traces)

    def __len__(self):
        return len(self.traces)

    def copy(self):
        return self.traces.copy()

    def insert(self, key: int, value: Trace):
        self.traces.insert(key, value)

    def sort(self, reverse: bool = False, key: Callable = lambda e: e.get_total_cost()):
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

    def tokenize(
        self,
        Token: Type[Observation],
        ObsLists: Type[ObservedTraceList] = ObservedTraceList,
        **kwargs,
    ):
        """Tokenizes the steps in this trace.

        Args:
            Token (Observation):
                A subclass of `Observation`, defining the method of tokenization
                for the steps.
            ObsLists (Type[ObservationLists]):
                The type of `ObservationLists` to be used. Defaults to the base `ObservationLists`.
        """
        return ObsLists(self, Token, **kwargs)

    def print(self, view="details", filter_func=lambda _: True, wrap=None):
        """Pretty prints the trace list in the specified view.

        Arguments:
            view ("details" | "color"):
                Specifies the view format to print in. "details" prints a
                detailed summary of each step in a trace. "color" prints a
                color grid, mapping fluents in a step to either red or green
                corresponding to the truth value. "actions" prints the actions
                in the traces.
        """
        views = ["details", "color", "actions"]
        if view not in views:
            warn(f'Invalid view {view}. Defaulting to "details".')
            view = "details"

        for trace in self:
            trace.print(view, filter_func, wrap)
