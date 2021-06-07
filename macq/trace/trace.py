from dataclasses import dataclass
from typing import List, Type, Iterable, Callable, Set
from inspect import cleandoc
from . import Action, Step, State
from ..observation import Observation


@dataclass
class SAS:
    pre_state: State
    action: Action
    post_state: State

    def __hash__(self):
        return hash(str(self.pre_state) + str(self.action) + str(self.post_state))


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
        def __init__(self, message):
            super().__init__(message)

    def __init__(self, steps: List[Step] = []):
        """Initializes a Trace with an optional list of steps.

        Args:
            steps (list):
                Optional; The list of steps in the trace. Defaults to an empty
                `list`.
        """
        self.steps = steps
        self.__reinit_actions_and_fluents()

    def __str__(self):
        indent = " " * 2
        # Summarize class attributes
        string = cleandoc(
            f"""
            Trace:
            {indent}Attributes:
            {indent*2}{len(self)} steps
            {indent*2}{len(self.fluents)} fluents
            {indent}Steps:
            """
        )
        string += "\n"

        # Dynamically get the spacing, 2n time
        state_len = max([len(str(step.state)) for step in self]) + 4
        string += f"{indent*2}{'Step':<5} {'State':^{state_len}} {'Action':<8}"
        string += "\n"

        # Create step string representation here, so formatting is consistent
        for i, step in enumerate(self):
            string += (
                f"{indent*2}{i+1:<5} {str(step.state):<{state_len}} "
                f"{str(step.action):<8}\n"
            )

        return string

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

    def __contains__(self, item: Step):
        return item in self.steps

    def append(self, item: Step):
        self.steps.append(item)
        self.__update_actions_and_fluents(item)

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

    def __update_actions_and_fluents(self, step: Step):
        print(type(step.state))
        self.fluents.update(step.state.keys())
        new_act = step.action
        if new_act is not None:
            self.actions.add(new_act)

    def __reinit_actions_and_fluents(self):
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

    def get_sas_triples(self, action: Action) -> Set[SAS]:
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
        sas_triples = set()
        for i, step in enumerate(self):
            if step.action == action:
                triple = SAS(step.state, action, self[i + 1].state)
                sas_triples.add(triple)
        return sas_triples

    def get_total_cost(self):
        """Calculates the total cost of this trace.

        Returns:
            The total cost of all actions performed in the trace.
        """
        sum = 0
        for step in self.steps:
            sum += step.action.cost
        return sum

    def get_slice_cost(self, start: int, end: int):
        """Calculates the total cost of a slice of this trace.

        Args:
            start (int):
                The start of the slice range. 1 <= start <= end.
            end: int
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
            sum += self.steps[i].action.cost
        return sum

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
        sum = 0
        for step in self:
            if step.action == action:
                sum += 1
        return sum / len(self)

    def tokenize(self, Token: Type[Observation], **kwargs):
        """Tokenizes the steps in this trace.

        Args:
            Token (Observation):
                A subclass of `Observation`, defining the method of tokenization
                for the steps.

        Returns:
            A list of observation tokens, corresponding to the steps in the
            trace.
        """

        observations: List[Observation] = []
        for step in self.steps:
            token = Token(step, **kwargs)
            observations.append(token)
        return observations
