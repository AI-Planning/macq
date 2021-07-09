from typing import Optional
from . import Action
from . import State


class Step:
    """A step in a Trace.

    A Step object stores a State and the action that is taken from the state.
    The final step in a trace will not have an action associated with it.

    Attributes:
        state (State):
            The state in this step.
        action (Action | None):
            The action taken from the state in this step.
        index (int):
            The "place" of the step in the trace.
    """

    def __init__(self, state: State, action: Optional[Action], index: int):
        """Initializes a Step with a state and optionally an action.

        Args:
            state (State):
                The state in this step.
            action (Action | None):
                The action taken from the state in this step. Must provide a
                value, but value can be None.
            index (int):
                The index of this step in the trace.
        """
        self.state = state
        self.action = action
        self.index = index
