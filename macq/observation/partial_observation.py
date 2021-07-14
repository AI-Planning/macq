from ..trace import Step, Fluent
from ..trace import PartialState
from . import Observation, InvalidQueryParameter
from typing import Set
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
            step = self.random_subset(step, **method_kwargs)
        elif method == "same":
            step = self.same_subset(step, **method_kwargs)

        self.state = step.state.clone()
        self.action = None if step.action is None else step.action.clone()

    def __eq__(self, other):
        return (
            isinstance(other, PartialObservation)
            and self.state == other.state
            and self.action == other.action
        )

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
            new_fluents[f] = None if f in hide_fluents_ls else step.state[f]
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
                new_fluents[f] = None if f in hide_fluents else step.state[f]
        return Step(PartialState(new_fluents), step.action, step.index)

    def get_all_base_fluents(self):
        """Returns a set of the details all the fluents used at the current step. The value of the fluents is not included."""
        fluents = set()
        for f in self.state.fluents:
            fluents.add(str(f)[1:-1])
        return fluents

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return self.action.details() == value
        elif key == "fluent_holds":
            return self.state.holds(value)
        else:
            raise InvalidQueryParameter(PartialObservation, key)
