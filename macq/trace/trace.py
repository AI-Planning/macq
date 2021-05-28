from dataclasses import dataclass
from typing import List, Type, Iterable, Callable
from inspect import cleandoc
from . import Action, Step, State
from ..observation import Observation


@dataclass
class SAS:
    pre_state: State
    action: Action
    post_state: State


class Trace:
    """
    Class for a Trace, which consists of each Step in a generated solution.

    """

    class InvalidCostRange(Exception):
        """
        Exception raised for incorrect user input for the cost range.
        """

        def __init__(self, message):
            super().__init__(message)

    def __init__(self, steps: List[Step] = []):
        """
        Creates a Trace object.

        Arguments
        ---------
        steps : List of Steps (optional)
            The list of Step objects that make up the trace.

        Attributes
        ----------
        num_steps : int
            The number of steps used.
        num_fluents : int
            The number of fluents used.
        fluents : List of str
            The list of the names of all fluents used.
            Information on the values of fluents are found in the steps.
        actions: List of Actions
            The list of the names of all actions used.
            Information on the preconditions/effects of actions are found in the steps.
        observations: List of Observations
            The set of observation tokens, tokenized from the steps.
        """
        self.steps = steps
        self.num_steps = len(steps)
        self.fluents = self._get_fluents()
        self.actions = self._get_actions()
        self.num_fluents = len(self.fluents)
        self.observations = []

    def __str__(self):
        string = cleandoc(
            f"""
            Trace:
                Attributes:
                    {self.num_steps} steps
                    {self.num_fluents} fluents
                Steps:
            """
        )
        string += "\n"

        # Dynamically get the spacing, 2n time
        state_len = max([len(str(step.state)) for step in self]) + 4
        string += f"        {'Step':<5} {'State':^{state_len}} {'Action':<8}\n"

        for i, step in enumerate(self):
            string += f"        {i+1:<5} {str(step.state):<{state_len}} {str(step.action):<8}\n"

        return string

    def __len__(self):
        return len(self.steps)

    def __setitem__(self, key: int, value: Step):
        self.steps[key] = value

    def __getitem__(self, key: int):
        return self.steps[key]

    def __delitem__(self, key: int):
        del self.steps[key]
        self.update()

    def __iter__(self):
        return iter(self.steps)

    def __reversed__(self):
        return reversed(self.steps)

    def __contains__(self, item: Step):
        return item in self.steps

    def append(self, item: Step):
        self.steps.append(item)
        self.update()

    def clear(self):
        self.steps.clear()
        self.update()

    def copy(self):
        return self.steps.copy()

    def count(self, value: Step):
        return self.steps.count(value)

    def extend(self, iterable: Iterable[Step]):
        self.steps.extend(iterable)
        self.update()

    def index(self, value: Step):
        return self.steps.index(value)

    def insert(self, index: int, item: Step):
        self.steps.insert(index, item)
        self.update()

    def pop(self):
        result = self.steps.pop()
        self.update()
        return result

    def remove(self, value: Step):
        self.steps.remove(value)
        self.update()

    def reverse(self):
        self.steps.reverse()

    def sort(self, reverse: bool = False, key: Callable = lambda e: e.action.cost):
        self.steps.sort(reverse=reverse, key=key)

    def add_steps(self, steps: List[Step]):
        """
        Class for a Trace, which consists of each Step in a generated solution.

        Arguments
        ---------
        steps : List of Steps (optional)
            The list of Step objects to be added to the trace.
        """
        self.steps.extend(steps)

    def _get_fluents(self):
        """
        Retrieves the fluents used in this trace.

        Returns
        -------
        list : Fluent
            Returns a list of all the fluents used in this trace.
        """
        fluents = set()
        for step in self:
            for fluent in step.state.fluents:
                fluents.add(fluent)
        return list(fluents)

    def _get_actions(self):
        """
        Retrieves the actions used in this trace.

        Returns
        -------
        list : Action
            Returns a list of all the actions used in this trace.
        """
        actions = set()
        for step in self.steps:
            actions.add(step.action)
        return list(actions)

    def get_prev_states(self, action: Action):
        """
        Returns a list of the states of the trace before this action took place.

        Arguments
        ---------
        action : Action
            An `Action` object.

        Returns
        -------
        prev_states : List of States
            A list of states before this action took place.
        """
        prev_states = []
        for step in self.steps:
            if step.action == action:
                prev_states.append(step.state)
        return prev_states

    def get_post_states(self, action: Action):
        """
        Returns a list of the states of the trace after the given action took place.

        Arguments
        ---------
        action : Action
            An `Action` object.

        Returns
        -------
        post_states : List of States
            A list of states after this action took place.
        """
        post_states = []
        for i in range(self.num_steps - 1):
            if self.steps[i].action == action:
                post_states.append(self.steps[i + 1].state)
        return post_states

    def get_sas_triples(self, action: Action) -> List[SAS]:
        """
        Returns a list of tuples where each tuple contains the state of the trace
        before the action, the action, and the state of the trace after the action.

        Arguments
        ---------
        action : Action
            An `Action` object.

        Returns
        -------
        sas_triples : List of tuples
            A list of tuples in the format (previous state, action, post-state).
        """
        sas_triples = []
        for i, step in enumerate(self):
            if step.action == action:
                triple = SAS(step.state, action, self[i + 1].state)
                sas_triples.append(triple)

        return sas_triples

    def get_total_cost(self):
        """
        Returns the total cost of all actions used in this Trace.

        Returns
        -------
        sum : int
            The total cost of all actions used.
        """
        sum = 0
        for step in self.steps:
            sum += step.action.cost
        return sum

    def get_cost_range(self, start: int, end: int):
        """
        Returns the total cost of the actions in the specified range of this Trace.
        The range starts at 1 and ends at the number of steps.

        Arguments
        ---------
        start : int
            The start of the specified range.
        end: int
            The end of the specified range.

        Returns
        -------
        sum : int
            The total cost of all actions in the specified range.
        """

        if start < 1 or end < 1 or start > self.num_steps or end > self.num_steps:
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
        """
        Returns the percentage of the number of times this action was used compared to the total
        number of actions taken.

        Arguments
        ---------
        action : Action
            An `Action` object.

        Returns
        -------
        percentage : float
            The percentage of the number of times this action was used compared to the total
            number of actions taken.
        """
        sum = 0
        for step in self.steps:
            if step.action == action:
                sum += 1
        return sum / self.num_steps

    def tokenize(self, Token: Type[Observation], **kwargs):
        """
        Creates the observation tokens using the token provided by the Observation.

        Arguments
        ---------
        Token : Observation subclass
            An `Observation` subclass.
        """
        
        for step in self.steps:
            token = Token(step=step, **kwargs)
            self.observations.append(token)

    def update(self):
        self.num_steps = len(self.steps)
        self.fluents = self.base_fluents()
        self.actions = self.base_actions()
        self.num_fluents = len(self.fluents)
        # update the placements of each step
        for i in range(len(self.steps)):
