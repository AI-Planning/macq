from ..trace.Step import Step


class Observation:
    """
    An ObservationToken object implements a `tokenize` function to generate an
    observation token for an action-state pair.
    """

    def __init__(self, step: Step):
        """
        Creates an ObservationToken object based on the supplied token method
        (defaults to identity). This will store the supplied tokenize method
        to use on steps.
        """
        self.step = step
