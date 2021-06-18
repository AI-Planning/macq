from ..trace import Step, Fluent
from ..trace import PartialState
from . import Observation
from typing import Callable, Union, Set
import random


class PercentError(Exception):
    """Raised when the user attempts to supply an invalid percentage of fluents to hide."""

    def __init__(
        self,
        message="The percentage supplied is invalid.",
    ):
        super().__init__(message)


class PartialObservabilityToken(Observation):
    """The Partial Observability Token.

    The partial observability token stores the step where some of the values of
    the fluents in the step's state are unknown. Inherits the base Observation
    class.
    """

    def __init__(
        self,
        step: Step,
        method: Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs
    ):
        """
        Creates an PartialObservabilityToken object, storing the step.

        Args:
            step (Step):
                The step associated with this observation.
            method (function reference):
                The method to be used to tokenize the step.
            **method_kwargs (keyword arguments):
                The arguments to be passed to the corresponding method function.
        """
        super().__init__(index=step.index)
        self.step = method(self, step, **method_kwargs)

    def __eq__(self, value):
        if isinstance(value, PartialObservabilityToken):
            return self.step == value.step
        return False

    def random_subset(self, step: Step, percent_missing: float):
        """Method of tokenization that picks a random subset of fluents to hide.

        Args:
            step (Step):
                The step to tokenize.
            percent_missing (float):
                The percentage of fluents to hide.

        Returns:
            The new step created using a PartialState that takes the hidden fluents into account.
        """
        if percent_missing > 1 or percent_missing < 0:
            raise PercentError()

        fluents = step.state.fluents
        num_new_fluents = int(len(fluents) * (percent_missing))

        new_fluents = {}
        # shuffle keys and take an appropriate subset of them
        fluents_list = list(fluents)
        random.shuffle(fluents_list)
        fluents_list = fluents_list[:num_new_fluents]
        # get new dict
        for f in fluents_list:
            new_fluents[f] = step.state[f]
        return Step(PartialState(new_fluents), step.action, step.index)

    def same_subset(self, step: Step, hide_fluents: Set[Fluent]):
        """Method of tokenization that hides the same subset of fluents every time.

        Args:
            step (Step):
                The step to tokenize.
            hide_fluents (Set[Fluent]):
                The set of fluents that will be hidden each time.

        Returns:
            The new step created using a PartialState that takes the hidden fluents into account.
        """
        new_fluents = {}
        for fluent in step.state.fluents:
            if fluent not in hide_fluents:
                new_fluents[fluent] = step.state[fluent]
        return Step(PartialState(new_fluents), step.action, step.index)
