from . import Observation
from ..trace import Step


class IDObservation(Observation):
    def __init__(self, step: Step, **kwargs):
        super().__init__(index=step.index, **kwargs)
        self.id = hash(step.state)

    def __hash__(self):
        return self.id
