from . import State

class PartiallyObservableState:
    """
    Class for a Partial State, which is a State where the value of some fluents are unknown.

    Arguments
    ---------
    fluents : List of Fluents
            A list of fluents representing the state.
    """

    def __init__(self, fluents: List[Fluent]):
       super().__init__(fluents)
    #def random_subset(self):
        