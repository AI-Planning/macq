from . import State
from ..core import GroundedFluent
from typing import Dict, Union


class PartialState(State):
    """A Partial State where the value of some fluents are unknown."""

    def __init__(self, fluents: Dict[GroundedFluent, Union[bool, None]] = {}):
        """
        Args:
            fluents (dict):
                Optional; A mapping of `GroundedFluent` objects to their value in this
                state. Defaults to an empty `dict`.
        """
        self.fluents = fluents
