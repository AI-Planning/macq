from ..trace import Step
from . import Observation


class IdentityObservation(Observation):
    def __init__(self, step: Step):
        super().__init__(step)
        self.token = step
