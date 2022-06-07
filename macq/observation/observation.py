from warnings import warn
from json import dumps
from typing import Union
import random
from ..trace import State, Action


class InvalidQueryParameter(Exception):
    def __init__(self, obs, param, message=None):
        if message is None:
            message = f"{param} is not a valid query parameter for {obs.__name__}"
        super().__init__(message)


class Observation:
    """
    An Observation object stores an observation token representation of a step.

    Attributes:
        step (Step):
            The step associated with this observation.
        index (int):
            The index of the associated step in the trace it is a part of.
    """

    index: int
    state: Union[State, None]
    action: Union[Action, None]

    def __init__(self, **kwargs):
        """
        Creates an Observation object, storing the step as a token, as well as its index/"place"
        in the trace (which corresponds to that of the step).

        Args:
            step (Step):
                The step associated with this observation.
        """
        if "index" in kwargs.keys():
            self.index = kwargs["index"]
        else:
            warn("Creating an Observation token without an index.")

    def __hash__(self):
        string = str(self)
        if string == "Observation\n":
            warn("Observation has no unique information. Generating a generic hash.")
        return hash(string)

    def __str__(self):
        out = "Observation\n"
        if self.index is not None:
            out += f"  Index: {str(self.index)}\n"
        if self.state:
            out += f"  State: {str(self.state)}\n"
        if self.action:
            out += f"  Action: {str(self.action)}\n"

        return out

    def get_details(self):
        ind = str(self.index) if self.index else "-"
        state = self.state.details() if self.state else "-"
        action = self.action.details() if self.action else ""
        return (ind, state, action)

    def _matches(self, *_):
        raise NotImplementedError()

    def extract_fluent_subset(self, state: State, percent: float):
        """Randomly extracts a subset of fluents from a state, according to the percentage given.

        Args:
            fluents (State):
                The state to extract fluents from.
            percent (float):
                The percent of the state to be extracted.

        Returns:
            The random subset of fluents.
        """
        num_new_f = int(len(state) * (percent))

        # shuffle keys and take an appropriate subset of them
        extracted_f = list(state)
        random.shuffle(extracted_f)
        return extracted_f[:num_new_f]

    def matches(self, query: dict):
        return all([self._matches(key, value) for key, value in query.items()])

    def serialize(self):
        return dumps(self, default=lambda o: o.__dict__, indent=2)
