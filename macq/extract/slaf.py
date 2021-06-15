import bauhaus
from bauhaus import Encoding, proposition, constraint
from nnf import Var
import macq.extract as extract
from ..observation import PartialObservabilityTokenPropositions
from ..trace import ObservationList, Action

e = Encoding()


class Slaf:
    def __new__(cls, observations: ObservationList):
        """Creates a new Model object.

        Args:
            observations (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if observations.type is not PartialObservabilityTokenPropositions:
            raise extract.IncompatibleObservationToken(observations.type, Slaf)

    @proposition(e)
    class ActionPrecondition(object):
        def __init__(self, action: Action, fluent: Var):
            self.action = action.name
            self.fluent = fluent

    @proposition(e)
    class ActionEffect(object):
        def __init__(self, action: Action, fluent: Var):
            self.action = action.name
            self.fluent = fluent

    @proposition(e)
    class ActionNeutral(object):
        def __init__(self, action: Action, fluent: Var):
            self.action = action.name
            self.fluent = fluent
