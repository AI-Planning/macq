from typing import List, Type, Iterable, Callable
from . import Action
from . import Step
from . import State
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
        self.__reinit_actions_and_fluents()
        self.observations = []

    def __repr__(self):
        string = "TRACE:\n\nAttributes:"
        string += "\n\nBase Fluents:\n"
        for fluent in self.fluents:
            string += fluent + "\n"
        string += "\nBase Actions:\n"
        for action in self.actions:
            string += action + "\n"
        string += "\n\nSteps:"
        for i in range(len(self.steps)):
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
        self.__update_actions_and_fluents(item)

    def clear(self):
        self.steps.clear()
        self.fluents = []
        self.actions = []

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

    def __new_fluents_from_state(self, state: State):
        """
        Retrieves any new fluents (fluents not yet in this trace's list of fluents)
        from the given state.

        Args:
            state (State): the state to extract new fluents from.
        """
        new = []
        for fluent in state.fluents:
            name = fluent.name
            if name not in self.fluents and name not in new:
                new.append(name)
        return new

    def __new_action_from_step(self, step: Step):
        """
        Retrieves the action from the given step if the action is new (not yet in this
        trace's list of actions).

        Args:
            step (Step): the given step to extract the action from.
        """
        name = step.action.name
        if name not in self.actions:
            return name

    def __update_actions_and_fluents(self, step: Step):
        """
        Update this trace's actions and fluents after taking into account the action and
        fluents of the step just added.

        Args:
            step (Step): the step just added to the trace.
        """
        new_fluents = self.__new_fluents_from_state(step.state)
        if new_fluents:
            self.fluents.extend(new_fluents)
        new_act = self.__new_action_from_step(step)
        if new_act:
            self.actions.append(new_act)

    def __reinit_actions_and_fluents(self):
        self.fluents = []
        self.actions = []
        for step in self.steps:
            self.__update_actions_and_fluents(step)

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
        for i in range(len(self.steps) - 1):
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
        for i in range(len(self.steps)):
            if self.steps[i].action == action:
                triple.append(self.steps[i].state)
                triple.append(action)
                if i + 1 < len(self.steps):
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

        if start < 1 or end < 1 or start > len(self.steps) or end > len(self.steps):
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
        return sum / len(self.steps)

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
