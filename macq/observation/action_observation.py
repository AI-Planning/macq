from ..trace import Step
from . import InvalidQueryParameter, Observation


class ActionObservation(Observation):
    """The Action Sequence Observability Token.
    Only stores the ordered action sequence, dropping all stateful information.
    For use in LOCM suite algorithms.
    """

    def __init__(
        self,
        step: Step,
        **kwargs,
    ):
        """
        Creates an ActionObservation object, storing the step.
        Args:
            step (Step):
                The step associated with this observation.
        """

        Observation.__init__(self, index=step.index)

        self.state = None # stateless representation
        self.action = None if step.action is None else step.action.clone()

    def __eq__(self, other):
        return (
            isinstance(other, ActionObservation)
            and self.state == None  #
            and self.action == other.action
        )

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return self.action.details() == value
        elif key == "fluent_holds":
            if self.state is None:
                return value is None
            return self.state.holds(value)
        else:
            raise InvalidQueryParameter(ActionObservation, key)
