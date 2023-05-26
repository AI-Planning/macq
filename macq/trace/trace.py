from collections import defaultdict
from dataclasses import dataclass
from typing import List, Type, Iterable, Callable, Set
from inspect import cleandoc
from warnings import warn
from rich.table import Table
from rich.text import Text
from rich.console import Console
from . import Action, Step, State
from ..observation import Observation, NoisyPartialDisorderedParallelObservation
from ..utils import TokenizationError


@dataclass
class SAS:
    pre_state: State
    action: Action
    post_state: State

    def __hash__(self):
        return hash(
            str(self.pre_state.details())
            + self.action.details()
            + str(self.post_state.details())
        )


class Trace:
    """A state trace of a planning problem.

    A `list`-like object, where each element is a step of the state trace.

    Attributes:
        steps (list):
            The list of Step objcts constituting the trace.
        fluents (set):
            The set of fluents in the trace.
        actions (set):
            The set of actions in the trace.
    """

    class InvalidCostRange(Exception):
        """Raised when an invalid range to retrieve costs is provided."""

        def __init__(self, message):
            super().__init__(message)

    def __init__(self, steps: List[Step] = None):
        """Initializes a Trace with an optional list of steps.

        Args:
            steps (list):
                Optional; The list of steps in the trace. Defaults to an empty
                `list`.
        """
        self.steps = steps if steps is not None else []
        self.__reinit_actions_and_fluents()

    def __eq__(self, other):
        return isinstance(other, Trace) and self.steps == other.steps

    def __len__(self):
        return len(self.steps)

    def __setitem__(self, key: int, value: Step):
        self.steps[key] = value

    def __getitem__(self, key: int):
        return self.steps[key]

    def __delitem__(self, key: int):
        del self.steps[key]

    def __iter__(self):
        return iter(self.steps)

    def __reversed__(self):
        return reversed(self.steps)

    def __contains__(self, step: Step):
        return step in self.steps

    def append(self, step: Step):
        self.steps.append(step)
        self.__update_actions_and_fluents(step)

    def clear(self):
        self.steps.clear()
        self.fluents = set()
        self.actions = set()

    def copy(self):
        return self.steps.copy()

    def count(self, value: Step):
        return self.steps.count(value)

    def extend(self, iterable: Iterable[Step]):
        self.steps.extend(iterable)
        for step in iterable:
            self.__update_actions_and_fluents(step)

    def index(self, value: Step):
        return self.steps.index(value)

    def insert(self, index: int, item: Step):
        self.steps.insert(index, item)
        self.__update_actions_and_fluents(item)

    def pop(self):
        result = self.steps.pop()
        self.__reinit_actions_and_fluents()
        return result

    def remove(self, value: Step):
        self.steps.remove(value)
        self.__reinit_actions_and_fluents()

    def reverse(self):
        self.steps.reverse()

    def sort(self, reverse: bool = False, key: Callable = lambda e: e.action.cost):
        self.steps.sort(reverse=reverse, key=key)

    def details(self, wrap=False):
        indent = " " * 2
        # Summarize class attributes
        details = Table.grid(expand=True)
        details.title = "Trace"
        details.add_column()
        details.add_row(
            cleandoc(
                f"""
            Attributes:
            {indent}{len(self)} steps
            {indent}{len(self.fluents)} fluents
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

        for step in self:
            action = step.action.details() if step.action else ""
            steps.add_row(str(step.index), step.state.details(), action)

        details.add_row(steps)

        return details

    def colorgrid(self, filter_func=lambda _: True, wrap=True):
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
                    "|" if i < len(self) and (i + 1) % 5 == 0 else " "
                    for i in range(len(self))
                ]
            ),
        )

        static = self.get_static_fluents()
        fluents = list(
            filter(
                filter_func,
                sorted(
                    self.fluents,
                    key=lambda f: float("inf") if f in static else len(str(f)),
                ),
            )
        )

        for fluent in fluents:
            step_str = ""
            for step in self:
                if step.state[fluent]:
                    step_str += "[green]"
                else:
                    step_str += "[red]"
                step_str += "■"

            colorgrid.add_row(str(fluent), step_str)

        return colorgrid

    def get_printable(self, view="details", filter_func=lambda _: True, wrap=None):
        """Returns a printable representation of the trace in the specified view."""
        views = ["details", "color", "actions"]
        if view not in views:
            warn(f'Invalid view {view}. Defaulting to "details".')
            view = "details"

        if view == "details":
            if wrap is None: wrap = False
            return self.details(wrap=wrap)
        elif view == "color":
            if wrap is None: wrap = True
            return self.colorgrid(filter_func=filter_func, wrap=wrap)
        elif view == "actions":
            return [step.action for step in self]


    def print(self, view="details", filter_func=lambda _: True, wrap=None):
        """Pretty prints the trace in the specified view.

        Arguments:
            view ("details" | "color" | "actions"):
                Specifies the view format to print in. "details" prints a
                detailed summary of each step in a trace. "color" prints a
                color grid, mapping fluents in a step to either red or green
                corresponding to the truth value. "actions" prints the actions
                in the trace.
            filter_func (Callable):
                A function used to filter the fluents to be printed.
            wrap (bool):
                Specifies whether or not to wrap the text in the printed output.
        """
        console = Console()
        console.print(self.get_printable(view=view, filter_func=filter_func, wrap=wrap))
        print()

    def get_static_fluents(self):
        fstates = defaultdict(list)
        for step in self:
            for f, v in step.state.items():
                fstates[f].append(v)

        static = set()
        for f, states in fstates.items():
            if all(states) or not any(states):
                static.add(f)

        return static

    def __update_actions_and_fluents(self, step: Step):
        """Updates the actions and fluents stored in this trace with any new ones from
        the provided step.

        Args:
            step (Step):
                The step to extract the possible new fluents and actions from.
        """
        self.fluents.update(step.state.keys())
        if step.action:
            self.actions.add(step.action)

    def __reinit_actions_and_fluents(self):
        """Reinitializes the actions and fluents stored in this trace, taking all current
        steps into account.
        """
        self.fluents = set()
        self.actions = set()
        for step in self.steps:
            self.__update_actions_and_fluents(step)

    def get_pre_states(self, action: Action):
        """Retrieves the list of states prior to the action in this trace.

        Args:
            action (Action):
                The action to retrieve pre-states for.

        Returns:
            The set of states prior to the action being performed in this
            trace.
        """
        prev_states = set()
        for step in self:
            if step.action == action:
                prev_states.add(step.state)
        return prev_states

    def get_post_states(self, action: Action):
        """Retrieves the list of states after the action in this trace.

        Args:
            action (Action):
                The action to retrieve post-states for.

        Returns:
            The set of states after the action was performed in this trace.
        """
        post_states = set()
        for i, step in enumerate(self):
            if step.action == action:
                post_states.add(self[i + 1].state)
        return post_states

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
        for i, step in enumerate(self):
            if step.action == action:
                triple = SAS(step.state, action, self[i + 1].state)
                sas_triples.append(triple)
        return sas_triples

    def get_total_cost(self):
        """Calculates the total cost of this trace.

        Returns:
            The total cost of all actions performed in the trace.
        """
        sum = 0
        for step in self.steps:
            if step.action:
                sum += step.action.cost
        return sum

    def get_slice_cost(self, start: int, end: int):
        """Calculates the total cost of a slice of this trace.

        Args:
            start (int):
                The start of the slice range. 1 <= start <= end.
            end (int):
                The end of the slice range. start <= end <= n, where n is the
                length of the trace (number of steps).

        Returns:
            The total cost of the slice of the trace.
        """

        if start < 1 or end < 1 or start > len(self) or end > len(self):
            raise self.InvalidCostRange(
                "Range supplied goes out of the feasible range."
            )
        if start > end:
            raise self.InvalidCostRange(
                "The start boundary must be smaller than the end boundary."
            )

        sum = 0
        for i in range(start - 1, end):
            if self[i].action:
                sum += self[i].action.cost
        return sum

    def get_steps(self, action: Action):
        """Retrieves all the Steps in the trace that use the specified action.

        Args:
            action (Action):
                The Action to retrieve corresponding steps for.

        Returns:
            The set of steps that use the specified action.

        """
        steps = set()
        for step in self:
            if step.action == action:
                steps.add(action)
        return steps

    def get_usage(self, action: Action):
        """Calculates how often an action was performed in this trace.

        Args:
            action (Action):
                The action to find the usage of.

        Returns:
            The frequency of the action in this trace. A percentage, calculated
            as the number of occurences of the action divided by the length of
            the trace (number of steps).
        """
        return len(self.get_steps(action)) / len(self)

    def tokenize(self, Token: Type[Observation], **kwargs):
        """Tokenizes the steps in this trace.

        Args:
            Token (Observation):
                A subclass of `Observation`, defining the method of tokenization
                for the steps.
            **kwargs (keyword arguments):
                Keyword arguments to pass into the Token function as parameters.

        Returns:
            A list of observation tokens, corresponding to the steps in the
            trace.
        """
        if Token == NoisyPartialDisorderedParallelObservation:
            raise TokenizationError(Token)
        return [Token(step=step, **kwargs) for step in self]
