from typing import List
from . import Fluent


class State:
    """
    Class for a State, which is the set of all fluents and their values at a particular Step.

    Arguments
    ---------
    fluents : List of Fluents
            A list of fluents representing the state.
    """

    def __init__(self, fluents: List[Fluent]):
        self.fluents = fluents

    def __repr__(self):
        string = "State:\n\n"
        for fluent in self.fluents:
            string += str(fluent) + "\n"
        string = string.strip()
        return string
