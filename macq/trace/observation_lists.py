from collections import defaultdict
from logging import warn
from typing import Callable, List, Type, Set
from inspect import cleandoc
from rich.console import Console
from rich.table import Table
from rich.text import Text
from . import Trace, Action, SAS
from ..observation import Observation
import macq.trace as TraceAPI


class ObservationLists(TraceAPI.TraceList):
    traces: List[List[Observation]]
    # Disable methods
    generate_more = property()
    get_usage = property()
    tokenize = property()
    get_fluents = property()

    def __init__(self, traces: TraceAPI.TraceList, Token: Type[Observation], **kwargs):
        self.traces = []
        self.type = Token
        trace: Trace
        for trace in traces:
            tokens = trace.tokenize(Token, **kwargs)
            self.append(tokens)

    def fetch_observations(self, query: dict):
        matches: List[Set[Observation]] = list()
        trace: List[Observation]
        for i, trace in enumerate(self):
            matches.append(set())
            for obs in trace:
                if obs.matches(query):  # if no matches, set can be empty
                    matches[i].add(obs)
        return matches  # list of sets of matching fluents from each trace

    def fetch_observation_windows(self, query: dict, left: int, right: int):
        windows = []
        matches = self.fetch_observations(query)
        trace: Set[Observation]
        for i, trace in enumerate(matches):  # note obs.index starts at 1 (index = i+1)
            for obs in trace:
                start = obs.index - left - 1
                end = obs.index + right
                windows.append(self[i][start:end])
        return windows

    def get_transitions(self, action: str):
        query = {"action": action}
        return self.fetch_observation_windows(query, 0, 1)

    def get_all_transitions(self):
        actions = set()
        for trace in self:
            for obs in trace:
                action = obs.action
                if action:
                    actions.add(action)
        # Actions in the observations can be either Action objects or strings depending on the type of observation
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

        obs_lists = []
        if view == "details":
            if wrap is None:
                wrap = False
            obs_lists = [self._details(obs_list, wrap=wrap) for obs_list in self]

        elif view == "color":
            if wrap is None:
                wrap = True
            obs_lists = [
                self._colorgrid(obs_list, filter_func=filter_func, wrap=wrap)
                for obs_list in self
            ]

        for obs_list in obs_lists:
            console.print(obs_list)
            print()

    def _details(self, obs_list: List[Observation], wrap: bool):
        indent = " " * 2
        # Summarize class attributes
        details = Table.grid(expand=True)
        details.title = "Trace"
        details.add_column()
        details.add_row(
            cleandoc(
                f"""
            Attributes:
            {indent}{len(obs_list)} steps
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

        for obs in obs_list:
            action = obs.action.details() if obs.action else ""
            steps.add_row(str(obs.index), obs.state.details(), action)

        details.add_row(steps)

        return details

    @staticmethod
    def _colorgrid(obs_list: List[Observation], filter_func: Callable, wrap: bool):
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
                    "|" if i < len(obs_list) and (i + 1) % 5 == 0 else " "
                    for i in range(len(obs_list))
                ]
            ),
        )

        static = ObservationLists.get_obs_static_fluents(obs_list)
        fluents = list(
            filter(
                filter_func,
                sorted(
                    ObservationLists.get_obs_fluents(obs_list),
                    key=lambda f: float("inf") if f in static else len(str(f)),
                ),
            )
        )

        for fluent in fluents:
            step_str = ""
            for obs in obs_list:
                if obs.state[fluent]:
                    step_str += "[green]"
                else:
                    step_str += "[red]"
                step_str += "■"

            colorgrid.add_row(str(fluent), step_str)

        return colorgrid

    @staticmethod
    def get_obs_fluents(obs_list: List[Observation]):
        fluents = set()
        for obs in obs_list:
            fluents.update(list(obs.state.keys()))
        return fluents

    @staticmethod
    def get_obs_static_fluents(obs_list: List[Observation]):
        fstates = defaultdict(list)
        for obs in obs_list:
            for f, v in obs.state.items():
                fstates[f].append(v)

        static = set()
        for f, states in fstates.items():
            if all(states) or not any(states):
                static.add(f)

        return static

    def get_sas_triples(self, action: Action) -> List[SAS]:
        """Retrieves the list of (S,A,S') triples for the action in this trace.

        In a (S,A,S') triple, S is the pre-state, A is the action, and S' is
        the post-state.

        Args:
            action (Action):
                The action to retrieve (S,A,S') triples for.

        Returns:
            A `SAS` object, containing the `pre_state`, `action`, and
            `post_state`.
        """
        sas_triples = []
        for obs_list in self:
            for i, obs in enumerate(obs_list):
                if obs.action == action:
                    triple = SAS(obs.state, action, self[i + 1].state)
                    sas_triples.append(triple)
        return sas_triples
