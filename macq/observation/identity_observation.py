from ..trace import Step
from . import Observation


class IdentityObservation(Observation):
    """The Identity Observation Token.

    The identity observation stores the step unmodified. Inherits the base Observation
    class.
    """

    def __init__(self, step: Step):
        """Creates an IdentityObservation object, storing the step.

        Args:
            step (Step):
                The step associated with this observation.
        """
        super().__init__(step)

    def __eq__(self, value):
        if isinstance(value, IdentityObservation):
            return self.step == value.step
        return False
