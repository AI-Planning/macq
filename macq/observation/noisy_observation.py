from . import Observation
from ..trace import Step
from ..utils import PercentError  # , extract_fluent_subset


class NoisyObservation(Observation):
    """The Noisy Observability Token.

    The noisy observability token stores the step where some of the values of
    the fluents in the step's state are incorrect (noisy).

    This token can be used to create states that are noisy but fully observable.
    """

    def __init__(self, step: Step, percent_noisy: float = 0):
        """
        Creates an NoisyObservation object, storing the state and action.

        Args:
            step (Step):
                The step associated with this observation.
            percent_noisy (float):
                The percentage of fluents to randomly make noisy in the observation.
        """

        super().__init__(index=step.index)

        if percent_noisy > 1 or percent_noisy < 0:
            raise PercentError()

        step = self.random_noisy_subset(step, percent_noisy)

        self.state = step.state.clone()
        self.action = None if step.action is None else step.action.clone()

    def random_noisy_subset(self, step: Step, percent_noisy: float):
        """Generates a random subset of fluents corresponding to the percent provided
        and flips their value to create noise.

        Args:
            step (Step):
                The step associated with this observation.
            percent_noisy (float):
                The percentage of fluents to randomly make noisy in the observation.

        Returns:
            A new `Step` with the noisy fluents in place.
        """
        # hidden fluents cannot be made noisy; only use visible fluents
        state = step.state.clone()
        invisible_f = {f for f in state if state[f] is None}
        visible_f = state.clone()
        for f in invisible_f:
            del visible_f[f]
        noisy_f = self.extract_fluent_subset(visible_f, percent_noisy)
        for f in state:
            state[f] = not state[f] if f in noisy_f else state[f]
        return Step(state, step.action, step.index)
