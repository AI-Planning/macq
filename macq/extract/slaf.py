import bauhaus
import macq.extract as extract
from bauhaus import Encoding, proposition, constraint
from nnf import Var, true, false
from typing import Union
from ..observation import PartialObservabilityTokenPropositions, Observation
from ..trace import Action, ObservationList

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
        Slaf.as_strips_slaf(observations)

    @proposition(e)
    class ActPrecond(object):
        def __init__(self, action: Union[Action, None], fluent: Var):
            if action:
                action = action.name
            self.action = action
            self.fluent = fluent

    @proposition(e)
    class ActEff(object):
        def __init__(self, action: Union[Action, None], fluent: Var):
            if action:
                action = action.name
            self.action = action
            self.fluent = fluent

    @proposition(e)
    class ActNeutral(object):
        def __init__(self, action: Union[Action, None], fluent: Var):
            if action:
                action = action.name
            self.action = action
            self.fluent = fluent

    @staticmethod
    def get_initial_fluent_factored(observation: Observation):
        raw_fluent_factored = []
        fluents = set()
        fluents.update(
            f for token in observation for f in token.get_base_true_fluents()
        )
        # set up the initial fluent factored form for the problem
        for f in fluents:
            phi = {}
            phi["fluent"] = f
            phi["pos expl"] = true
            phi["neg expl"] = true
            phi["neutral"] = true
            raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def as_strips_slaf(observations: ObservationList):
        global e
        ActPrecond = Slaf.ActPrecond
        ActEff = Slaf.ActEff
        ActNeutral = Slaf.ActNeutral
        # iterate through every observation in the list of observations/traces
        for obs in observations:
            # get the fluent factored formula for this observation/trace
            raw_fluent_factored = Slaf.get_initial_fluent_factored(obs)
            # iterate through all tokens (action/observation pairs) in this observation/trace
            for token in obs:
                a = token.step.action
                all_o = token.step.state.children
                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF
                for phi in raw_fluent_factored:
                    f = phi["fluent"]
                    pos_precond = ActPrecond(a, f).compile()
                    neg_precond = ActPrecond(a, ~f).compile()
                    pos_effect = ActEff(a, f).compile()
                    neg_effect = ActEff(a, ~f).compile()
                    neutral = ActNeutral(a, f).compile()
                    phi["neutral"] = (
                        (~pos_precond | phi["pos expl"])
                        & (~neg_precond | phi["neg expl"])
                        & phi["neutral"]
                    )
                    phi["pos expl"] = pos_effect | (
                        neutral & ~neg_precond & phi["pos expl"]
                    )
                    phi["neg expl"] = neg_effect | (
                        neutral & ~pos_precond & phi["neg expl"]
                    )
                    # apply the constraints to this action and all fluents (Section 5.2, 1-3)
                    constraint.add_exactly_one(e, pos_effect, neg_effect, neutral)
                    constraint.add_at_most_one(e, pos_precond, neg_precond)
                # steps 1. (d)-(e) of AS-STRIPS-SLAF
                for phi in raw_fluent_factored:
                    f = phi["fluent"]
                    if f in all_o:
                        phi["pos expl"] = true
                        phi["neg expl"] = false
                        phi["neutral"] = phi["neutral"] & phi["pos expl"]
                    if ~f in all_o:
                        phi["pos expl"] = ~f | false
                        phi["neg expl"] = f | true
                        phi["neutral"] = phi["neutral"] & phi["neg expl"]
            # convert to formula once you have stepped through the whole observation/trace and applied all transformations
            # add as constraints to e here
            for phi in raw_fluent_factored:
                f = phi["fluent"]
                # convert to formula for each fluent
                e.add_constraint(
                    (~f | phi["pos expl"]) & (f | phi["neg expl"]) & phi["neutral"]
                )
        print(type(e))
        e = e.compile()
        print(e)
