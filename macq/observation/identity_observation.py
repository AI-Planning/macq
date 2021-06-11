from ..trace import Step
from . import Observation, InvalidQueryParameter


class IdentityObservation(Observation):
    """
    The identity observation stores the step unmodified.
    """

    def __init__(self, step: Step, **kwargs):
        """
        Creates an IdentityObservation object, storing the step.

        Attributes
        ----------
        step : Step
            The step associated with this observation.
        """
        super().__init__(index=step.index, **kwargs)
        self.state = step.state.clone()
        self.action = None if step.action is None else step.action.clone()

    def __str__(self):
        return str(self.index) + str(self.action) + str(self.state)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, IdentityObservation):
            return False
        return self.state == other.state and self.action == other.action

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return self.action.name == value
        elif key == "fluent_holds":
            return self.state.holds(value)  # whatever this needs to look like
        else:
            raise InvalidQueryParameter(IdentityObservation, key)
