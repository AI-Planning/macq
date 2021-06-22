import bauhaus
import macq.extract as extract
from bauhaus import Encoding, proposition, constraint
from typing import Union, List
from ..observation import Observation, PartialObservabilityToken
from ..trace import Action, ObservationList

e = Encoding()


@proposition(e)
class BauhausFluent(object):
    """The proposition that allows basic fluents to be used in the bauhaus encoding."""

    def __init__(self, details: str):
        """Creates a bauhaus fluent.

        Args:
            details (str):
                Describes the fluent/its objects (the value of the fluent, however, is not held by the fluent itself.)
        """
        self.details = details

    def __repr__(self):
        return self.details

    def __eq__(self, other):
        return other.__class__ == self.__class__ and other.details == self.details

    def __hash__(self):
        return hash(self.details)


@proposition(e)
class ActPrecond(object):
    """The proposition that allows action preconditions to be used in the bauhaus encoding."""

    def __init__(
        self, action: Union[Action, None], fluent: BauhausFluent, fluent_val: bool
    ):
        """Creates an action precondition proposition.

        Args:
            action (Union[Action, None]):
                The relevant action.
            fluent (BauhausFluent):
                The fluent to be set as a precondition of the action.
            fluent_val (bool):
                The True/False value of the fluent. If the value is False, then the negation of the fluent is set to the precondition of the action.
        """
        act_str = None
        if action:
            act_str = f"{action.name}"
            for obj in action.obj_params:
                act_str += f" {obj.details()}"
        self.action = act_str
        self.fluent = fluent
        self.fluent_val = fluent_val

    def details(self):
        """Returns a string with the action proposition's details."""
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
    """The proposition that allows action effects to be used in the bauhaus encoding."""

    def __init__(
        self, action: Union[Action, None], fluent: BauhausFluent, fluent_val: bool
    ):
        """Creates an action effect proposition.

        Args:
            action (Union[Action, None]):
                The relevant action.
            fluent (BauhausFluent):
                The fluent to be set as an effect of the action.
            fluent_val (bool):
                The True/False value of the fluent. If the value is False, then the negation of the fluent is set to the effect of the action.
        """
        act_str = None
        if action:
            act_str = f"{action.name}"
            for obj in action.obj_params:
                act_str += f" {obj.details()}"
        self.action = act_str
        self.fluent = fluent
        self.fluent_val = fluent_val

    def details(self):
        """Returns a string with the action proposition's details."""
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
    """The proposition that allows neutral actions (actions that have no effect on propositions) to be used in the bauhaus encoding."""

    def __init__(self, action: Union[Action, None], fluent: BauhausFluent):
        """Creates an neutral action effect proposition.

        Args:
            action (Union[Action, None]):
                The relevant action.
            fluent (BauhausFluent):
                The fluent to be set as a neutral effect of the action (that is, the action, has no effect on the fluent).
        """
        act_str = None
        if action:
            act_str = f"{action.name}"
            for obj in action.obj_params:
                act_str += f" {obj.details()}"
        self.action = act_str
        self.fluent = fluent

    def details(self):
        """Returns a string with the action proposition's details."""
        return f"{self.action} has no effect on {self.fluent}"

    def __repr__(self):
        return self.details()

    def __hash__(self):
        return hash(self.details())


@proposition(e)
class FalseProp(object):
    """Proposition that is always false (bottom symbol)."""

    def __init__(self):
        self.prop = False

    def __repr__(self):
        return "false"

    def __hash__(self):
        return hash("false")


@proposition(e)
class TrueProp(object):
    """Proposition that is always true."""

    def __init__(self):
        self.prop = True

    def __repr__(self):
        return "true"

    def __hash__(self):
        return hash("true")


class Slaf:
    # only need one true and one false
    true = TrueProp()
    false = FalseProp()

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
    def __get_initial_fluent_factored(
        observation: Observation, raw_fluent_factored: Union[List, None]
    ):
        """Gets the initial fluent-factored formula of an observation/trace.

        Args:
            observation (Observation):
                The observation to extract the fluent-factored formula from.

        Returns:
            A list of dictionaries that holds the fluent-factored formula.
        """
        true = Slaf.true
        false = Slaf.false
        if not raw_fluent_factored:
            raw_fluent_factored = []
        fluents = set()

        all_fluents = [f for token in observation for f in token.get_all_base_fluents()]
        for f in all_fluents:
            fluents.add(f)

        # get previous fluents
        old_fluents = set()
        for f in raw_fluent_factored:
            old_fluents.add(f["fluent"].details)

        # set up the initial fluent factored form for the problem
        for f in fluents:
            if f not in old_fluents:
                phi = {}
                phi["fluent"] = BauhausFluent(f)
                phi["pos expl"] = true
                phi["neg expl"] = true
                phi["neutral"] = true
                raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def as_strips_slaf(observations: ObservationList):
        """Implements the AS-STRIPS-SLAF algorithm from section 5.3 of the SLAF paper.
        Iterates through the action/observation pairs of each observation/trace, returning
        a fluent-factored transition belief formula that filters according to that action/observation.
        The transition belif formulas for each trace/observation are conjoined to get one final formula,
        which is then solved using a SAT solver to extract models.

        Args:
            observations (ObservationList):
                The list of observations/traces to apply the filtering algorithm to.
        """
        global e
        true = Slaf.true
        false = Slaf.false
        # sets to hold action propositions
        precond = {}
        effects = {}
        neutrals = {}
        raw_fluent_factored = None
        # iterate through every observation in the list of observations/traces
        for obs in observations:
            # get the fluent factored formula for this observation/trace
            raw_fluent_factored = Slaf.__get_initial_fluent_factored(
                obs, raw_fluent_factored
            )
            # iterate through all tokens (action/observation pairs) in this observation/trace
            for token in obs:
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
                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF, page 366
                # "if a" ensures that the action is not None (happens on the last step of a trace)
                a = token.step.action
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

                        # only update the dictionaries if necessary
                        keys = precond.keys()
                        if pos_pre_det not in keys:
                            precond[pos_pre_det] = pos_precond
                        if neg_pre_det not in keys:
                            precond[neg_pre_det] = neg_precond
                        keys = effects.keys()
                        if pos_eff_det not in keys:
                            effects[pos_eff_det] = pos_effect
                        if neg_eff_det not in keys:
                            effects[neg_eff_det] = neg_effect
                        keys = neutrals.keys()
                        if neut_det not in keys:
                            neutrals[neut_det] = neutral

                        # apply appropriate changes
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
        # keys = list(e.keys())
        # keys = [str(f) for f in keys]
        # keys.sort()
        for key, val in e.items():
            f.write(str(key) + ": " + str(val) + "\n")
        # for key in keys:
        #    f.write(str(key) + "\n")
        f.close()
