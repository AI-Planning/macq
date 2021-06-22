import bauhaus
import macq.extract as extract
from bauhaus import Encoding, proposition, constraint
from typing import Union
from ..observation import Observation, PartialObservabilityToken
from ..trace import Action, ObservationList

e = Encoding()


@proposition(e)
class BauhausFluent(object):
    def __init__(self, details: str):
        self.details = details

    def __repr__(self):
        return self.details

    def __eq__(self, other):
        return other.__class__ == self.__class__ and other.details == self.details

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


@proposition(e)
class FalseConstr(object):
    def __init__(self):
        self.fluent = False

    def __repr__(self):
        return "false"


@proposition(e)
class TrueConstr(object):
    def __init__(self):
        self.fluent = True

    def __repr__(self):
        return "true"


true = TrueConstr()
false = FalseConstr()


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
        if observations.type is not PartialObservabilityToken:
            raise extract.IncompatibleObservationToken(observations.type, Slaf)
        Slaf.as_strips_slaf(observations)

    @staticmethod
    def __get_initial_fluent_factored(observation: Observation):
        global true
        raw_fluent_factored = []
        fluents = set()

        all_fluents = [f for token in observation for f in token.get_all_base_fluents()]
        for f in all_fluents:
            fluents.add(f)

        # set up the initial fluent factored form for the problem
        for f in fluents:
            phi = {}
            phi["fluent"] = BauhausFluent(f)
            phi["pos expl"] = true
            phi["neg expl"] = true
            phi["neutral"] = true
            raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def as_strips_slaf(observations: ObservationList):
        global e, true, false
        # dicts to hold action propositions
        precond = {}
        effects = {}
        neutrals = {}
        # iterate through every observation in the list of observations/traces
        for obs in observations:
            # get the fluent factored formula for this observation/trace
            raw_fluent_factored = Slaf.__get_initial_fluent_factored(obs)
            # iterate through all tokens (action/observation pairs) in this observation/trace
            for token in obs:
                a = token.step.action
                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF, page 366
                # "if a" ensures that the action is not None (happens on the last step of a trace)
                if a:
                    for phi in raw_fluent_factored:
                        f = phi["fluent"]
                        pos_precond = ActPrecond(a, f, True)
                        neg_precond = ActPrecond(a, f, False)
                        pos_effect = ActEff(a, f, True)
                        neg_effect = ActEff(a, f, False)
                        neutral = ActNeutral(a, f)
                        pos_pre_det = pos_precond.details()
                        neg_pre_det = neg_precond.details()
                        pos_eff_det = pos_effect.details()
                        neg_eff_det = neg_effect.details()
                        neut_det = neutral.details()
                        precond[pos_pre_det] = pos_precond
                        precond[neg_pre_det] = neg_precond
                        effects[pos_eff_det] = pos_effect
                        effects[neg_eff_det] = neg_effect
                        neutrals[neut_det] = neutral

                        phi["neutral"] = (
                            (~precond[pos_pre_det] | phi["pos expl"])
                            & (~precond[neg_pre_det] | phi["neg expl"])
                            & phi["neutral"]
                        )
                        phi["pos expl"] = effects[pos_eff_det] | (
                            neutrals[neut_det] & ~precond[neg_pre_det] & phi["pos expl"]
                        )
                        phi["neg expl"] = effects[neg_eff_det] | (
                            neutrals[neut_det] & ~precond[pos_pre_det] & phi["neg expl"]
                        )
                        # apply the constraints to this action and all fluents (Section 5.2, 1-3)
                        constraint.add_exactly_one(
                            e,
                            effects[pos_eff_det],
                            effects[neg_eff_det],
                            neutrals[neut_det],
                        )
                        constraint.add_at_most_one(
                            e, precond[pos_pre_det], precond[neg_pre_det]
                        )
                # steps 1. (d)-(e) of AS-STRIPS-SLAF
                # NEED TO CHECK THE VALUE OF THE FLUENT HERE
                all_o = [
                    BauhausFluent(f.details())
                    if token.step.state[f]
                    else ~BauhausFluent(f.details())
                    for f in token.step.state.fluents
                ]

                for phi in raw_fluent_factored:
                    f = phi["fluent"]
                    for o in all_o:
                        # "negated" fluents are of type CustomNNF, and all f are of type BauhausFluent
                        if f == o:
                            phi["pos expl"] = true
                            phi["neg expl"] = false
                            phi["neutral"] = phi["neutral"] & phi["pos expl"]
                        if isinstance(o, bauhaus.core.CustomNNF):
                            if (~f).compile() == o.compile():
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

        e = e.compile()
        # e = e.simplify()
        e = e.solve()
        f = open("output.txt", "w")
        keys = list(e.keys())
        keys = [str(f) for f in keys]
        keys.sort()
        # for key, val in e.items():
        #    f.write(str(key) + ": " + str(val) + "\n")
        for key in keys:
            f.write(str(key) + "\n")
        f.close()
