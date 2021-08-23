from logging import warning
from ..trace import Step, Fluent
from . import PartialObservation, Observation
from typing import Set


class PercentError(Exception):
    """Raised when the user attempts to supply an invalid percentage of fluents to hide."""

    def __init__(
        self,
        message="The percentage supplied is invalid.",
    ):
        super().__init__(message)


class AtomicPartialObservation(PartialObservation):
    """The Atomic Partial Observability Token.
    The atomic partial observability token stores the step where some of the values of
    the fluents in the step's state are unknown. Inherits the base Observation
    class. Unlike the partial observability token, the atomic partial observability token
    stores everything in strings.
    """

    def __init__(
        self, step: Step, percent_missing: float = 0, hide: Set[Fluent] = None
    ):
        """
        Creates an AtomicPartialObservation object, storing the step.

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
            warning("Creating a PartialObseration with no missing information.")

        Observation.__init__(self, index=step.index)

        if percent_missing < 1:
            step = self.hide_random_subset(step, percent_missing)
        if hide:
            step = self.hide_subset(step, hide)

        self.state = None if percent_missing == 1 else step.state.clone(atomic=True)
        self.action = None if step.action is None else step.action.clone(atomic=True)

    def __eq__(self, other):
        return (
            isinstance(other, AtomicPartialObservation)
            and self.state == other.state
            and self.action == other.action
        )

    def details(self):
        return f"Obs {str(self.index)}.\n  State: {str(self.state)}\n  Action: {str(self.action)}"
