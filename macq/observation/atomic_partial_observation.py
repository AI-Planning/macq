from ..trace import Step, Fluent
from ..trace import PartialState
from . import Observation, InvalidQueryParameter
from typing import Callable, Union, Set, List, Optional
from dataclasses import dataclass
import random


class PercentError(Exception):
    """Raised when the user attempts to supply an invalid percentage of fluents to hide."""

    def __init__(
        self,
        message="The percentage supplied is invalid.",
    ):
        super().__init__(message)


class AtomicPartialObservation(Observation):
    """The Atomic Partial Observability Token.

    The atomic partial observability token stores the step where some of the values of
    the fluents in the step's state are unknown. Inherits the base Observation
    class. Unlike the partial observability token, the atomic partial observability token
    stores everything in strings.
    """

    # used these to store action and state info with just strings
    class IdentityState(dict):
        def __hash__(self):
            return hash(tuple(sorted(self.items())))

    @dataclass
    class IdentityAction:
        name: str
        obj_params: List[str]
        cost: Optional[int]

        def __str__(self):
            objs_str = ""
            for o in self.obj_params:
                objs_str += o + " "
            return " ".join([self.name, objs_str]) + "[" + str(self.cost) + "]"

        def __hash__(self):
            return hash(str(self))

    def __init__(
        self,
        step: Step,
        method: Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs,
    ):
        """
        Creates an PartialObservation object, storing the step.

        Args:
            step (Step):
                The step associated with this observation.
            method (function reference):
                The method to be used to tokenize the step.
            **method_kwargs (keyword arguments):
                The arguments to be passed to the corresponding method function.
        """
        super().__init__(index=step.index)
        step = method(self, step, **method_kwargs)
        self.state = self.IdentityState(
            {str(fluent): value for fluent, value in step.state.items()}
        )
        self.action = (
            None
            if step.action is None
            else self.IdentityAction(
                step.action.name,
                list(map(lambda o: o.details(), step.action.obj_params)),
                step.action.cost,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, AtomicPartialObservation):
            return False
        return self.state == other.state and self.action == other.action

    # and here is the old matches function

    def _matches(self, key: str, value: str):
        if key == "action":
            if self.action is None:
                return value is None
            return str(self.action) == value
        elif key == "fluent_holds":
            return self.state[value]
        else:
            raise InvalidQueryParameter(AtomicPartialObservation, key)

    def details(self):
        return f"Obs {str(self.index)}.\n  State: {str(self.state)}\n  Action: {str(self.action)}"

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
