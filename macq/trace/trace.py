from typing import List
from .Action import Action
from .Step import Step


class Trace:
    """
    Class for a Trace, which consists of each Step in a generated solution.

    Arguments
    ---------
    steps : list of Steps
        The list of Step objects that make up the trace.

    Other Class Attributes:
    num_fluents : int
        The number of fluents used.
    fluents : list of str
        The list of the names of all fluents used.
        Information on the values of fluents are found in the steps.
    actions: list of Actions
        The list of the names of all actions used.
        Information on the preconditions/effects of actions are found in the steps.

    """

    def __init__(self, steps: List[Step]):
        self.steps = steps
        self.num_fluents = len(steps)
        self.fluents = self.base_fluents()
        self.actions = self.base_actions()

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
        Returns the state of the trace before this action.

        Arguments
        ---------
        action : Action
            An `Action` object.

        Returns
        -------
        state : list of Steps
            A list of Steps before this action took place.
        """
        prev_states = []
        for step in self.steps:
            if step.action == action:
                prev_states.append(step.state)
        return prev_states

    def get_post_states(self, action: Action):
        """
        Returns the state of the trace after this Action.

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
