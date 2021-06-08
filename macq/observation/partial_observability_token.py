from ..trace import Step, Fluent
from ..trace import PartialState
from . import Observation
from typing import Callable, Union, Set
import random


class PartialObservabilityToken(Observation):
    """
    The partial observability token stores the step where some of the values of
    the fluents in the step's state are unknown.
    """

    def __init__(
        self,
        step: Step,
        method=Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs
    ):
        """
        Creates an PartialObservabilityToken object, storing the step.

        Attributes
        ----------
        step : Step
            The step associated with this observation.
        """
        super().__init__(method(self, step, **method_kwargs))

    def __eq__(self, value):
        if isinstance(value, PartialObservabilityToken):
            return self.step == value.step
        return False

    def random_subset(self, step: Step, percent_missing=int):
        fluents = step.state.fluents
        num_new_fluents = int(len(fluents) * (percent_missing / 100))
        new_fluents = {}
        while len(new_fluents) < num_new_fluents:
            ran_fluent = random.choice(list(fluents.keys()))
            new_fluents[ran_fluent] = fluents[ran_fluent]
        new_state = PartialState(new_fluents)
        return Step(new_state, step.action, step.index)

    def same_subset(self):
        new_fluents = {}
        pass
