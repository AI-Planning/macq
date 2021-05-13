from ..trace.Step import Step
from ObservationToken import ObservationToken


class IdentityToken(ObservationToken):
    def __init__(self):
        pass

    def tokenize(self, step: Step) -> Step:
        """
        The identity `tokenize` function.

        Arguments
        ---------
        step : Step
        A step object to generate an observation token for.

        Returns
        -------
        step : Step
        The supplied step object.
        """
        return step
