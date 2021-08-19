from logging import warning
from json import dumps

import random
from ..trace import State


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
            warning("Creating an Observation token without an index.")

    def _matches(self, *_):
        raise NotImplementedError()

    def extract_fluent_subset(self, fluents: State, percent: float):
        num_new_f = int(len(fluents) * (percent))

        # shuffle keys and take an appropriate subset of them
        extracted_f = list(fluents)
        random.shuffle(extracted_f)
        return extracted_f[:num_new_f]

    def matches(self, query: dict):
        return all([self._matches(key, value) for key, value in query.items()])

    def serialize(self):
        return dumps(self, default=lambda o: o.__dict__, indent=2)
