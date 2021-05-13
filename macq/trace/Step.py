class Step:
    """
    A Step object stores the action, and state prior to the action for a step
    in a trace.
    """

    def __init__(self, action: Action, state: List[Fluent]):
        """
        Creates a Step object. This stores action, and state prior to the
        action.

        Attributes
        ----------
        action : Action
            The action taken in this step.
        state : list
            A list of fluents representing the state.
        """
        self.action = action
        self.state = state
