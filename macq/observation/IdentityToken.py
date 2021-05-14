from ..trace.Step import Step
from ObservationToken import ObservationToken


class IdentityObservation(Observation):
    def __init__(self, step: Step):
        super().__init__(step)
        # if this wasn't identity there would be more processing before
        # assigning self.token
        self.token = step
