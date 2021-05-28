from typing import List, Type, Iterable, Callable
from . import Action
from . import Step
from ..observation import Observation


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
        self.fluents = self.base_fluents()
        self.actions = self.base_actions()
        self.num_fluents = len(self.fluents)
        self.observations = []

    def __repr__(self):
        string = "TRACE:\n\nAttributes:\n\nNumber of Steps: " + str(self.num_steps)
        string += "\nNumber of Fluents: " + str(self.num_fluents)
        string += "\n\nBase Fluents:\n"
        for fluent in self.fluents:
            string += fluent + "\n"
        string += "\nBase Actions:\n"
        for action in self.actions:
            string += action + "\n"
        string += "\n\nSteps:"
        for i in range(self.num_steps):
            string += "\n\nSTEP " + str(i + 1) + ":\n\n" + str(self.steps[i]) + "\n"
        string += "\nObservations:\n"
        for obs in self.observations:
            string += "\n" + str(obs)
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

    def base_fluents(self):
        """
        Retrieves the names of all fluents used in this trace.

        Returns
        -------
        list : str
            Returns a list of the names of all fluents used in this trace.
        """
        fluents = []
        for step in self.steps:
            for fluent in step.state.fluents:
                name = fluent.name
                if name not in fluents:
                    fluents.append(name)
        return fluents

    def base_actions(self):
        """
        Retrieves the names of all actions used in this trace.

        Returns
        -------
        list : str
            Returns a list of the names of all actions used in this trace.
        """
        actions = []
        for step in self.steps:
            name = step.action.name
            if name not in actions:
                actions.append(name)
        return actions

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

    def get_sas_triples(self, action: Action):
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
        triple = []
        for i in range(self.num_steps):
            if self.steps[i].action == action:
                triple.append(self.steps[i].state)
                triple.append(action)
                if i + 1 < self.num_steps:
                    triple.append(self.steps[i + 1].state)
                triple = tuple(triple)
                sas_triples.append(triple)
                triple = []

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

    def tokenize(self, Token: Type[Observation]):
        """
        Creates the observation tokens using the token provided by the Observation.

        Arguments
        ---------
        Token : Observation subclass
            An `Observation` subclass.
        """
        for step in self.steps:
            token = Token(step)
            self.observations.append(token)

    def update(self):
        self.num_steps = len(self.steps)
        self.fluents = self.base_fluents()
        self.actions = self.base_actions()
        self.num_fluents = len(self.fluents)