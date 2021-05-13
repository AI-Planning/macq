from typing import List
import macq
from macq.trace.Action import Action
from macq.trace.State import State

class Step:
    """
    A Step object stores the action, and state prior to the action for a step
    in a trace.
    """

    def __init__(self, action: Action, state: State):
        """
        Creates a Step object. This stores action, and state prior to the
        action.

        Attributes
        ----------
        action : Action
            The action taken in this step.
        state : State
            The state (list of fluents) at this step.
        """
        self.action = action
        self.state = state
