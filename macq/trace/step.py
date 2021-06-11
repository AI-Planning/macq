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
        """
        self.state = state
        self.action = action
        self.index = index

    def __str__(self):
        string = str(self.action) + "\n\n" + str(self.state)
        return string

    def base_fluents(self):
        # Is this useful? Not used anywhere
        # Each extract method has its own "get fluents"
        # if we want a general get fluents shouldn't it be on TraceList?
        fluents = []
        for fluent in self.state.fluents:
            fluents.append(fluent.name)
        return fluents

    def base_action(self):
        # Is this useful? Not used anywhere
        # could just do trace[i].action.name
        return self.action.name
