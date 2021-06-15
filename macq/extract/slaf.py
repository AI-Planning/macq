import bauhaus
from bauhaus import Encoding, proposition, constraint
from nnf import Var, true
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
        Slaf.get_initial_fluent_factored(observations)

    @staticmethod
    def get_initial_fluent_factored(observations: ObservationList):
        fluent_factored = None
        for obs in observations:
            for token in obs:
                for f in token.step.state:
                    if fluent_factored and f in fluent_factored.vars():
                        continue
                    if not f.true:
                        f = ~f
                    conj = (~f | true) & (f | true) & true
                    print(conj)
                    conj = conj.make_smooth()
                    print(conj)
                    if fluent_factored:
                        fluent_factored = fluent_factored & conj
                    else:
                        fluent_factored = conj
        print(fluent_factored)
        return fluent_factored

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
