from __future__ import annotations
from collections import defaultdict
from collections.abc import MutableSequence
from warnings import warn
from typing import Callable, Dict, List, Type, Set, TYPE_CHECKING
from inspect import cleandoc
from rich.console import Console
from rich.table import Table
from rich.text import Text

from . import Observation
from ..trace import Action, Fluent

# Prevents circular importing
if TYPE_CHECKING:
    from macq.trace import TraceList


class MissingToken(Exception):
    def __init__(self, message=None):
        if message is None:
            message = (
                f"Cannot create ObservationLists from a TraceList without a Token."
            )
        super().__init__(message)


class TokenTypeMismatch(Exception):
    def __init__(self, token, obs_type, message=None):
        if message is None:
            message = (
                "Token type does not match observation tokens."
                f"Token type: {token}"
                f"Observation type: {obs_type}"
            )
        super().__init__(message)


class ObservedTraceList(MutableSequence):
    """A sequence of observations.

    A `list`-like object, where each element is a list of `Observation`s.

    Attributes:
        observations (List[List[Observation]]):
            The internal list of lists of `Observation` objects.
        type (Type[Observation]):
            The type (class) of the observations.
    """

    observations: List[List[Observation]]
    type: Type[Observation]

    def __init__(
        self,
        trace_list: TraceList = None,
        Token: Type[Observation] = None,
        observations: List[List[Observation]] = None,
        **kwargs,
    ):
        if trace_list is not None:
            if not Token and not observations:
                raise MissingToken()

            if Token:
                self.type = Token

            self.observations = []
            self.tokenize(trace_list, **kwargs)

            if observations:
                self.extend(observations)
                # Check that the observations are of the specified token type
                if self.type and type(observations[0][0]) != self.type:
                    raise TokenTypeMismatch(self.type, type(observations[0][0]))
                # If token type was not provided, infer it from the observations
                elif not self.type:
                    self.type = type(observations[0][0])

        elif observations:
            self.observations = observations
            self.type = type(observations[0][0])

        else:
            self.observations = []
            self.type = Observation

    def __getitem__(self, key: int):
        return self.observations[key]

    def __setitem__(self, key: int, value: List[Observation]):
        self.observations[key] = value
        if self.type == Observation:
            self.type = type(value[0])
        elif type(value[0]) != self.type:
            raise TokenTypeMismatch(self.type, type(value[0]))

    def __delitem__(self, key: int):
        del self.observations[key]

    def __iter__(self):
        return iter(self.observations)

    def __len__(self):
        return len(self.observations)

    def insert(self, key: int, value: List[Observation]):
        self.observations.insert(key, value)
        if self.type == Observation:
            self.type = type(value[0])
        elif type(value[0]) != self.type:
            raise TokenTypeMismatch(self.type, type(value[0]))

    def get_actions(self) -> Set[Action]:
        actions: Set[Action] = set()
        for obs_trace in self:
            for obs in obs_trace:
                action = obs.action
                if action is not None:
                    actions.add(action)
        return actions

    def get_fluents(self) -> Set[Fluent]:
        fluents: Set[Fluent] = set()
        for obs_trace in self:
            for obs in obs_trace:
                if obs.state:
                    fluents.update(list(obs.state.keys()))
        return fluents

    def tokenize(self, trace_list: TraceList, **kwargs):
        for trace in trace_list:
            tokens = trace.tokenize(self.type, **kwargs)
            self.append(tokens)

    def fetch_observations(self, query: dict) -> List[Set[Observation]]:
        matches: List[Set[Observation]] = []
        for i, obs_trace in enumerate(self.observations):
            matches.append(set())
            for obs in obs_trace:
                if obs.matches(query):
                    matches[i].add(obs)
        return matches

    def fetch_observation_windows(
        self, query: dict, left: int, right: int
    ) -> List[List[Observation]]:
        windows = []
        matches = self.fetch_observations(query)
        for i, obs_set in enumerate(matches):
            for obs in obs_set:
                # NOTE: obs.index starts at 1
                start = obs.index - left - 1
                end = obs.index + right
                windows.append(self[i][start:end])
        return windows

    def get_transitions(self, action: str) -> List[List[Observation]]:
        query = {"action": action}
        return self.fetch_observation_windows(query, 0, 1)

    def get_all_transitions(self) -> Dict[Action, List[List[Observation]]]:
        actions = self.get_actions()
        try:
            return {
                action: self.get_transitions(action.details()) for action in actions
            }
        except AttributeError:
            return {action: self.get_transitions(str(action)) for action in actions}

    def print(self, view="details", filter_func=lambda _: True, wrap=None):
        """Pretty prints the trace list in the specified view.

        Arguments:
            view ("details" | "color"):
                Specifies the view format to print in. "details" provides a
                detailed summary of each step in a trace. "color" provides a
                color grid, mapping fluents in a step to either red or green
                corresponding to the truth value.
            filter_func (function):
                Optional; Used to filter which fluents are printed in the
                colorgrid display.
            wrap (bool):
                Determines if the output is wrapped or cut off. Details defaults
                to cut off (wrap=False), color defaults to wrap (wrap=True).
        """
        console = Console()

        views = ["details", "color"]
        if view not in views:
            warn(f'Invalid view {view}. Defaulting to "details".')
            view = "details"

        obs_tracelist = []
        if view == "details":
            if wrap is None:
                wrap = False
            obs_tracelist = [self._details(obs_trace, wrap=wrap) for obs_trace in self]

        elif view == "color":
            if wrap is None:
                wrap = True
            obs_tracelist = [
                self._colorgrid(obs_trace, filter_func=filter_func, wrap=wrap)
                for obs_trace in self
            ]

        for obs_trace in obs_tracelist:
            console.print(obs_trace)
            print()

    def _details(self, obs_trace: List[Observation], wrap: bool):
        indent = " " * 2
        # Summarize class attributes
        details = Table.grid(expand=True)
        details.title = "Trace"
        details.add_column()
        details.add_row(
            cleandoc(
                f"""
            Attributes:
            {indent}{len(obs_trace)} steps
            {indent}{len(self.get_fluents())} fluents
            """
            )
        )
        steps = Table(
            title="Steps", box=None, show_edge=False, pad_edge=False, expand=True
        )
        steps.add_column("Step", justify="right", width=8)
        steps.add_column(
            "State",
            justify="center",
            overflow="ellipsis",
            max_width=100,
            no_wrap=(not wrap),
        )
        steps.add_column("Action", overflow="ellipsis", no_wrap=(not wrap))

        for obs in obs_trace:
            ind, state, action = obs.get_details()
            steps.add_row(ind, state, action)

        details.add_row(steps)

        return details

    @staticmethod
    def _colorgrid(obs_trace: List[Observation], filter_func: Callable, wrap: bool):
        colorgrid = Table(
            title="Trace", box=None, show_edge=False, pad_edge=False, expand=False
        )
        colorgrid.add_column("Fluent", justify="right")
        colorgrid.add_column(
            header=Text("Step", justify="center"), overflow="fold", no_wrap=(not wrap)
        )
        colorgrid.add_row(
            "",
            "".join(
                [
                    "|" if i < len(obs_trace) and (i + 1) % 5 == 0 else " "
                    for i in range(len(obs_trace))
                ]
            ),
        )

        static = ObservedTraceList.get_obs_static_fluents(obs_trace)
        fluents = list(
            filter(
                filter_func,
                sorted(
                    ObservedTraceList.get_obs_fluents(obs_trace),
                    key=lambda f: float("inf") if f in static else len(str(f)),
                ),
            )
        )

        for fluent in fluents:
            step_str = ""
            for obs in obs_trace:
                if obs.state and obs.state[fluent]:
                    step_str += "[green]"
                else:
                    step_str += "[red]"
                step_str += "■"

            colorgrid.add_row(str(fluent), step_str)

        return colorgrid

    @staticmethod
    def get_obs_fluents(obs_trace: List[Observation]):
        fluents = set()
        for obs in obs_trace:
            if obs.state:
                fluents.update(list(obs.state.keys()))
        return fluents

    @staticmethod
    def get_obs_static_fluents(obs_trace: List[Observation]):
        fstates = defaultdict(list)
        for obs in obs_trace:
            if obs.state:
                for f, v in obs.state.items():
                    fstates[f].append(v)

        static = set()
        for f, states in fstates.items():
            if all(states) or not any(states):
                static.add(f)

        return static
