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
        self.state = {fluent.details(): value for fluent, value in step.state.items()}
        self.action = None if step.action is None else step.action.details()

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
            return self.action == value
        elif key == "fluent_holds":
            return self.state[value]
        else:
            raise InvalidQueryParameter(IdentityObservation, key)

    def details(self):
        return f"Obs {str(self.index)}.\n  State: {str(self.state)}\n  Action: {str(self.action)}"
