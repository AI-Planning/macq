import bauhaus
import macq.extract as extract
from bauhaus import Encoding, proposition, constraint
from typing import Union
from ..observation import PartialObservabilityTokenPropositions, Observation

# from ..observation.partial_observability_token_propositions import fluent
from ..trace import Action, ObservationList

e = Encoding()


@proposition(e)
class BauhausFluent(object):
    def __init__(self, details: str):
        self.details = details

    def __repr__(self):
        return self.details

    def __hash__(self):
        return hash(self.details)


@proposition(e)
class ActPrecond(object):
    def __init__(
        self, action: Union[Action, None], fluent: BauhausFluent, fluent_val: bool
    ):
        act_str = None
        if action:
            act_str = f"{action.name}"
            for obj in action.obj_params:
                act_str += f" {obj.details()}"
        self.action = act_str
        self.fluent = fluent
        self.fluent_val = fluent_val

    def details(self):
        return (
            f"{self.fluent} is a precondition of {self.action}"
            if self.fluent_val
            else f"~{self.fluent} is a precondition of {self.action}"
        )

    def __repr__(self):
        return self.details()

    def __hash__(self):
        return hash(self.details())


@proposition(e)
class ActEff(object):
    def __init__(
        self, action: Union[Action, None], fluent: BauhausFluent, fluent_val: bool
    ):
        act_str = None
        if action:
            act_str = f"{action.name}"
            for obj in action.obj_params:
                act_str += f" {obj.details()}"
        self.action = act_str
        self.fluent = fluent
        self.fluent_val = fluent_val

    def details(self):
        return (
            f"{self.action} causes {self.fluent}"
            if self.fluent_val
            else f"{self.action} causes ~{self.fluent}"
        )

    def __repr__(self):
        return self.details()

    def __hash__(self):
        return hash(self.details())


@proposition(e)
class ActNeutral(object):
    def __init__(self, action: Union[Action, None], fluent: BauhausFluent):
        act_str = None
        if action:
            act_str = f"{action.name}"
            for obj in action.obj_params:
                act_str += f" {obj.details()}"
        self.action = act_str
        self.fluent = fluent

    def details(self):
        return f"{self.action} has no effect on {self.fluent}"

    def __repr__(self):
        return self.details()

    def __hash__(self):
        return hash(self.details())


@proposition(e)
class FalseConstr(object):
    def __init__(self):
        self.fluent = False

    def __repr__(self):
        return "false"

    def __hash__(self):
        return hash("false")


@proposition(e)
class TrueConstr(object):
    def __init__(self):
        self.fluent = True

    def __repr__(self):
        return "true"

    def __hash__(self):
        return hash("true")


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

    @staticmethod
    def __get_initial_fluent_factored(observation: Observation):
        raw_fluent_factored = []
        fluents = set()
        fluents.update(
            f for token in observation for f in token.get_base_true_fluents()
        )

        # set up the initial fluent factored form for the problem
        for f in fluents:
            phi = {}
            phi["fluent"] = BauhausFluent(f)
            true = TrueConstr()
            phi["pos expl"] = true
            phi["neg expl"] = true
            phi["neutral"] = true
            raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def as_strips_slaf(observations: ObservationList):
        global e
        true = TrueConstr()
        false = FalseConstr()
        # sets to hold action propositions
        precond = set()

        # iterate through every observation in the list of observations/traces
        for obs in observations:
            # get the fluent factored formula for this observation/trace
            raw_fluent_factored = Slaf.__get_initial_fluent_factored(obs)
            # iterate through all tokens (action/observation pairs) in this observation/trace
            for token in obs:
                a = token.step.action
                all_o = [BauhausFluent(f) for f in token.step.state.fluents]
                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF
                if a:
                    for phi in raw_fluent_factored:
                        f = phi["fluent"]
                        pos_precond = ActPrecond(a, f, True)
                        neg_precond = ActPrecond(a, f, False)
                        pos_effect = ActEff(a, f, True)
                        neg_effect = ActEff(a, f, False)
                        neutral = ActNeutral(a, f)

                        # objects are registering as unique even though they ARE NOT.
                        # try to find a spot where a duplicate is about to be added, then compare their strings and hashes?
                        # those that have the same string should have the SAME HASH.

                        # sometimes pos_precond doesn't change...?

                        # print(len(precond))
                        # print(hash(str(pos_precond)))
                        if pos_precond in precond:
                            print("already in")
                        precond.add((pos_precond))
                        # print(len(precond))
                        if neg_precond in precond:
                            print("already in")
                        precond.add((neg_precond))
                        # print(len(precond))

                        # print(precond)
                        # print(pos_precond)
                        # print(neg_precond)

                        # print(precond)
                        # print()

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
            # print(precond)

        e = e.compile()
        e = e.simplify(merge_nodes=True)
        precond = list(precond)
        precond = [str(pre) for pre in precond]
        precond.sort()
        f = open("output.txt", "w")
        for pre in precond:
            f.write(pre)
            f.write("\n")
        # f.write(str(e))
        f.close()
        print(e.solve())
