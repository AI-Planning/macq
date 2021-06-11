from ..trace import Step


class Observation:
    """
    An Observation object stores an observation token representation of a step.

    Attributes:
        step (Step):
            The step associated with this observation.
        index (int):
            The index of the associated step in the trace it is a part of.
    """

    def __init__(self, step: Step):
        """
        Creates an Observation object, storing the step as a token, as well as its index/"place"
        in the trace (which corresponds to that of the step).

        Args:
            step (Step):
                The step associated with this observation.
        """
        self.step = step
        self.index = step.index
