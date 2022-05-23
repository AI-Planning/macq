from macq.observation.noisy_observation import NoisyObservation
from ..trace import Step, Fluent
from . import PartialObservation
from typing import Set


class NoisyPartialObservation(PartialObservation, NoisyObservation):
    """The Noisy Partial Observability Token.

    The noisy partial observability token stores the step where some of the values of
    the fluents in the step's state are incorrect (noisy) or unknown (partial). Inherits
    both the PartialObservation token class and the NoisyObservation token class.
    """

    def __init__(
        self,
        step: Step,
        percent_missing: float = 0,
        hide: Set[Fluent] = None,
        percent_noisy: float = 0,
        replace: bool = False,
    ):
        """
        Creates an NoisyPartialObservation object.

        Args:
            step (Step):
                The step associated with this observation.
            percent_missing (float):
                The percentage of fluents to randomly hide in the observation.
            hide (Set[Fluent]):
                The set of fluents to explicitly hide in the observation.
            percent_noisy (float):
                The percentage of fluents to randomly make noisy in the observation.
            replace (bool):
                Option to replace noisy fluents with the values of other existing fluents instead
                of just flipping their values.
        """
        # get state and action with missing fluents (updates self.state and self.action)
        PartialObservation.__init__(
            self, step=step, percent_missing=percent_missing, hide=hide
        )
        # get state and action with noisy fluents, using the updated state and action (then updates self.state and self.action)
        NoisyObservation.__init__(
            self,
            step=Step(self.state, self.action, step.index),
            percent_noisy=percent_noisy,
            replace=replace,
        )
