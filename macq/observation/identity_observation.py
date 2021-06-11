from ..trace import Step
from . import Observation


class IdentityObservation(Observation):
    """Identity Observation Token.

    The identity observation stores the step unmodified. Extends the base Observation
    class.

    Attributes:
        step (Step):
            The step associated with this observation.
    """

    def __init__(self, step: Step):
        """Creates an IdentityObservation object, storing the step."""
        super().__init__(step)

    def __eq__(self, value):
        if isinstance(value, IdentityObservation):
            return self.step == value.step
        return False
