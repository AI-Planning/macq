from . import State
from . import Fluent
from typing import Dict


class PartialState(State):
    """
    Class for a Partial State, which is a State where the value of some fluents are unknown.

    Args:
        fluents (dict):
            Optional; A mapping of `Fluent` objects to their value in this
            state. Defaults to an empty `dict`.
    """

    def __init__(self, fluents: Dict[Fluent, bool] = {}):
        super().__init__(fluents)
