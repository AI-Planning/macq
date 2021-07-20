from dataclasses import dataclass
from typing import Optional, List
from ..trace import Step
from . import Observation, InvalidQueryParameter


class IdentityObservation(Observation):
    """The Identity Observation Token.

    The identity observation stores the step unmodified. Inherits the base Observation
    class.
    """

    class IdentityState(dict):
        def __hash__(self):
            return hash(tuple(sorted(self.items())))

    @dataclass
    class IdentityAction:
        name: str
        obj_params: List[str]
        cost: Optional[int]

        def __str__(self):
            return self.name + str(self.obj_params) + str(self.cost)

        def __hash__(self):
            return hash(str(self))

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

    def details(self):
        return f"Obs {str(self.index)}.\n  State: {str(self.state)}\n  Action: {str(self.action)}"

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return self.action.details() == value
        elif key == "fluent_holds":
            return self.state.holds(value)
        else:
            raise InvalidQueryParameter(IdentityObservation, key)
