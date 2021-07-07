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


class PartialObservation(Observation):
    """The Partial Observability Token.

    The partial observability token stores the step where some of the values of
    the fluents in the step's state are unknown. Inherits the base Observation
    class.
    """

    def __init__(self, step: Step, method: str, **method_kwargs):
        """
        Creates an PartialObservation object, storing the step.

        Args:
            step (Step):
                The step associated with this observation.
            method (str):
                The method to be used to tokenize the step. "random" or "same".
            **method_kwargs (keyword arguments):
                The arguments to be passed to the corresponding method function.
        """
        super().__init__(index=step.index)
        if method == "random":
            self.step = self.random_subset(step, **method_kwargs)
        elif method == "same":
            self.step = self.same_subset(step, **method_kwargs)

    def __eq__(self, value):
        return isinstance(value, PartialObservation) and self.step == value.step

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
        hide_fluents_ls = list(fluents)
        random.shuffle(hide_fluents_ls)
        hide_fluents_ls = hide_fluents_ls[:num_new_fluents]
        # get new dict
        for f in fluents:
            if f in hide_fluents_ls:
                new_fluents[f] = None
            else:
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
        for f in step.state.fluents:
            if f in hide_fluents:
                new_fluents[f] = None
            else:
                new_fluents[f] = step.state[f]
        return Step(PartialState(new_fluents), step.action, step.index)

    def get_all_base_fluents(self):
        """Returns a set of the details all the fluents used at the current step. The value of the fluents is not included."""
        fluents = set()
        for f in self.step.state.fluents:
            fluents.add(str(f)[1:-1])
        return fluents
