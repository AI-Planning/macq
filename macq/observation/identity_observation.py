from ..trace import Step
from . import Observation


class IdentityObservation(Observation):
    """
    The identity observation stores the step unmodified.
    """

    def __init__(self, step: Step):
        """
        Creates an IdentityObservation object, storing the step.

        Attributes
        ----------
        step : Step
            The step associated with this observation.
        """
        super().__init__(step.index)
        self.state = step.state.clone()
        self.action = step.action.clone()

    def __eq__(self, other):
        if not isinstance(other, IdentityObservation):
            return False
        return self.state == other.state and self.action == other.action
