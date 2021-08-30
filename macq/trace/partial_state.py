from . import State
from . import Fluent
from typing import Dict, Union


class PartialState(State):
    """A Partial State where the value of some fluents are unknown."""

    def __init__(self, fluents: Dict[Fluent, Union[bool, None]] = {}):
        """
        Args:
            fluents (dict):
                Optional; A mapping of `Fluent` objects to their value in this
                state. Defaults to an empty `dict`.
        """
        self.fluents = fluents
