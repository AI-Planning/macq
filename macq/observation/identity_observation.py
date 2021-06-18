from ..trace import Step
from . import Observation, InvalidQueryParameter


class IdentityObservation(Observation):
    """The Identity Observation Token.

    The identity observation stores the step unmodified. Inherits the base Observation
    class.
    """

    def __init__(self, step: Step, **kwargs):
        """
        Creates an IdentityObservation object, storing the step.


        Args:
            step (Step):
                The step associated with this observation.
        """
        super().__init__(index=step.index, **kwargs)
        self.state = step.state.clone()
        self.action = None if step.action is None else step.action.clone()

    def __hash__(self):
        return hash(self.details())

    def __eq__(self, other):
        if not isinstance(other, IdentityObservation):
            return False
        return self.state == other.state and self.action == other.action

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return self.action.details() == value
        elif key == "fluent_holds":
            return self.state.holds(value)
        else:
            raise InvalidQueryParameter(IdentityObservation, key)

    def details(self):
        return str(self.index) + self.action.details() + self.state.details()
