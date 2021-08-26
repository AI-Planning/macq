from logging import warning
from ..utils import PercentError#, extract_fluent_subset
from ..trace import Step, Fluent
from ..trace import PartialState
from . import Observation, InvalidQueryParameter
from typing import Set


class PartialObservation(Observation):
    """The Partial Observability Token.

    The partial observability token stores the step where some of the values of
    the fluents in the step's state are unknown. Inherits the base Observation
    class.
    """

    def __init__(
        self, step: Step, percent_missing: float = 0, hide: Set[Fluent] = None
    ):
        """
        Creates an PartialObservation object, storing the step.

        Args:
            step (Step):
                The step associated with this observation.
            percent_missing (float):
                The percentage of fluents to randomly hide in the observation.
            hide (Set[Fluent]):
                The set of fluents to explicitly hide in the observation.
        """
        if percent_missing > 1 or percent_missing < 0:
            raise PercentError()

        if percent_missing == 0 and not hide:
            warning("Creating a PartialObservation with no missing information.")

        # necessary because multiple inheritance can change the parent of this class
        Observation.__init__(self, index=step.index)

        # If percent_missing == 1 -> self.state = None (below).
        # This allows ARMS (and other algorithms) to skip steps when there is no
        # state information available without having to check every mapping in
        # the state (slow in large domains).
        if percent_missing < 1:
            step = self.hide_random_subset(step, percent_missing)
        if hide:
            step = self.hide_subset(step, hide)

        self.state = None if percent_missing == 1 else step.state.clone()
        self.action = None if step.action is None else step.action.clone()

    def __eq__(self, other):
        return (
            isinstance(other, PartialObservation)
            and self.state == other.state
            and self.action == other.action
        )

    def hide_random_subset(self, step: Step, percent_missing: float):
        """Hides a random subset of the fluents in the step.

        Args:
            step (Step):
                The step to tokenize.
            percent_missing (float):
                The percentage of fluents to hide (0-1).

        Returns:
            A Step whose state is a PartialState with the random fluents hidden.
        """
        new_fluents = {}
        fluents = step.state.fluents
        hidden_f = self.extract_fluent_subset(fluents, percent_missing)
        # get new dict
        for f in fluents:
            new_fluents[f] = None if f in hidden_f else step.state[f]
        return Step(PartialState(new_fluents), step.action, step.index)

    def hide_subset(self, step: Step, hide: Set[Fluent]):
        """Hides the specified set of fluents in the observation.

        Args:
            step (Step):
                The step to tokenize.
            hide (Set[Fluent]):
                The set of fluents that will be hidden.

        Returns:
            A Step whose state is a PartialState with the specified fluents hidden.
        """
        new_fluents = {}
        for f in step.state.fluents:
            new_fluents[f] = None if f in hide else step.state[f]
        return Step(PartialState(new_fluents), step.action, step.index)

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return self.action.details() == value
        elif key == "fluent_holds":
            return self.state.holds(value)
        else:
            raise InvalidQueryParameter(PartialObservation, key)
