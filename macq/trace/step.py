from typing import Optional
from . import Action
from . import State


class Step:
    """
    A Step object stores the action, and state prior to the action for a step
    in a trace.
    """

    def __init__(self, action: Action, state: State, index: int):
    def __init__(self, state: State, action: Optional[Action]):
        """
        Creates a Step object. This stores action, and state prior to the
        action.

        Attributes
        ----------
        action : Action
            The action taken in this step.
        state : State
            The state (list of fluents) at this step.
        index : int
            The placement of this step within the trace.
        """
        self.action = action
        self.state = state
        self.index = index

    def __str__(self):
        string = str(self.action) + "\n\n" + str(self.state)
        return string

    def base_fluents(self):
        """
        Retrieves the names of all fluents used in this step.

        Returns
        -------
        list : str
            Returns a list of the names of all fluents used in this step.
        """
        fluents = []
        for fluent in self.state.fluents:
            fluents.append(fluent.name)
        return fluents

    def base_action(self):
        """
        Retrieves the name of the action used in this step.

        Returns
        -------
        list : str
            Returns the name of the action used in this step.
        """
        return self.action.name
