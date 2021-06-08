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
        method: Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs
    ):
        """
        Creates an PartialObservabilityToken object, storing the step.

        Attributes
        ----------
        step : Step
            The step associated with this observation.
        method : Callable function
            The method to be used to tokenize the step.
        **method_kwargs : keyword arguments
            The arguments to be passed to the corresponding method function.
        """
        super().__init__(method(self, step, **method_kwargs))

    def __eq__(self, value):
        if isinstance(value, PartialObservabilityToken):
            return self.step == value.step
        return False

    def random_subset(self, step: Step, percent_missing: int):
        """Method of tokenization that picks a random subset of fluents to hide.

        Args:
            step (Step): The step to tokenize.
            percent_missing (int): The percentage of fluents to hide.

        Returns:
            [Step]: The new step created using a PartialState that takes the hidden fluents into account.
        """
        fluents = step.state.fluents
        num_new_fluents = int(len(fluents) * (percent_missing / 100))
        new_fluents = {}
        while len(new_fluents) < num_new_fluents:
            ran_fluent = random.choice(list(fluents.keys()))
            new_fluents[ran_fluent] = step.state[ran_fluent]
        return Step(PartialState(new_fluents), step.action, step.index)

    def same_subset(self, step: Step, hide_fluents: Set[Fluent]):
        """Method of tokenization that hides the same subset of fluents every time.

        Args:
            step (Step): The step to tokenize.
            hide_fluents (Set[Fluent]): The set of fluents that will be hidden each time.

        Returns:
            [Step]: The new step created using a PartialState that takes the hidden fluents into account.
        """
        new_fluents = {}
        for fluent in step.state.fluents:
            if fluent not in hide_fluents:
                new_fluents[fluent] = step.state[fluent]
        return Step(PartialState(new_fluents), step.action, step.index)
