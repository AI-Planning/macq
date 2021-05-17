from ..trace import Step
from . import Observation

class IdentityObservation(Observation):
    def __init__(self, step: Step):
        super().__init__(step)
    def __eq__(self, value):
        if isinstance(value, IdentityObservation):
            return self.step == value.step
        return False