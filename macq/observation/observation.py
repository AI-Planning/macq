from ..trace import Step


class Observation:
    """
    An Observation object stores an observation token representation of a step.
    """

    def __init__(self, index: int):
        """
        Creates an Observation object, storing the step as a token, as well as its index/"place"
        in the trace (which corresponds to that of the step).
        """
        self.index = index
