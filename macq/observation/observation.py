from logging import warn
from ..trace import Step


class InvalidQueryParameter(Exception):
    def __init__(self, obs, param, message=None):
        if message is None:
            message = f"{param} is not a valid query parameter for {obs.__name__}"
        super().__init__(message)


class Observation:
    """
    An Observation object stores an observation token representation of a step.
    """

    def __init__(self, **kwargs):
        """
        Creates an Observation object, storing the step as a token, as well as its index/"place"
        in the trace (which corresponds to that of the step).
        """
        if "index" in kwargs.keys():
            self.index = kwargs["index"]
        else:
            warn("Creating an Observation token without an index.")

    def _matches(self, *_):
        raise NotImplementedError()

    def matches(self, query: dict):
        return all([self._matches(key, value) for key, value in query.items()])
