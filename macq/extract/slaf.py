import bauhaus
import macq.extract as extract
from bauhaus import Encoding, proposition, constraint
from bauhaus.core import CustomNNF, Or, And
from typing import Union, List, Set
from nnf import Var
from ..observation import Observation, PartialObservabilityToken
from ..trace import Action, ObservationList

e = Encoding()
other = Encoding()


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
class Bottom(object):
    """Proposition that is always false (bottom symbol)."""

    def __init__(self):
        self.prop = False

    def __repr__(self):
        return "bottom"

    def __hash__(self):
        return hash("bottom")


@proposition(e)
class Top(object):
    """Proposition that is always true (top symbol)."""

    def __init__(self):
        self.prop = True

    def __repr__(self):
        return "top"

    def __hash__(self):
        return hash("top")


class Slaf:
    # only need one true and one false
    top = Top()
    bottom = Bottom()

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
        Slaf.as_strips_slaf(observations, False)

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
        top = Slaf.top
        bottom = Slaf.bottom
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
                phi["pos expl"] = top
                phi["neg expl"] = top
                phi["neutral"] = top
                raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def __print_nested_formula(formula, strings: Set = None):
        """Unravels a nested formula and returns a set with a simple string representation of it.

        Args:
            formula (type And, Or, Var, or CustomNNF):
                The formula to unravel and form a simplified string version of.
        """
        if not strings:
            strings = set()
        formula = formula.simplify()
        for f in formula.children:
            if not isinstance(f, Var):
                Slaf.__print_nested_formula(f, strings)
            else:
                strings.add(str(f) + ": " + str(f.true))
        return strings

    @staticmethod
    def clear_encoding(e: Encoding):
        top = Slaf.top
        bottom = Slaf.bottom
        e.clear_constraints()
        e.clear_debug_constraints()
        # e.purge_propositions()
        e._custom_constraints = set()
        e.add_constraint(top & ~bottom)

    @staticmethod
    def as_strips_slaf(observations: ObservationList, debug: bool = True):
        """Implements the AS-STRIPS-SLAF algorithm from section 5.3 of the SLAF paper.
        Iterates through the action/observation pairs of each observation/trace, returning
        a fluent-factored transition belief formula that filters according to that action/observation.
        The transition belif formulas for each trace/observation are conjoined to get one final formula,
        which is then solved using a SAT solver to extract models.

        Args:
            observations (ObservationList):
                The list of observations/traces to apply the filtering algorithm to.
        """
        # get global variables
        global e
        top = Slaf.top
        bottom = Slaf.bottom
        clear_encoding = Slaf.clear_encoding
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
            if debug:
                all_f_details = [f["fluent"].details for f in raw_fluent_factored]
                all_f_details.sort()
                for f in all_f_details:
                    print(f)
                to_obs = []
                user_input = ""
                while user_input != "x":
                    user_input = input(
                        "Which fluents do you want to observe? Enter 'x' when you are finished.\n"
                    )
                    if user_input in all_f_details:
                        to_obs.append(user_input)
                        print(user_input + " added to the debugging list.")
                    else:
                        if user_input != "x":
                            print("The fluent you entered is invalid.")

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
                        clear_encoding(e)
                        # "negated" fluents are of type CustomNNF, and all f are of type BauhausFluent
                        if f == o:
                            phi["pos expl"] = top
                            phi["neg expl"] = bottom
                            e.add_constraint(phi["neutral"])
                            e.add_constraint(phi["pos expl"])
                            neutral_form = e.compile().simplify()
                            phi["neutral"] = neutral_form
                            # phi["neutral"] = phi["neutral"] & phi["pos expl"]
                        elif isinstance(o, CustomNNF):
                            if (~f).compile() == o.compile():
                                phi["pos expl"] = bottom
                                phi["neg expl"] = top
                                e.add_constraint(phi["neutral"])
                                e.add_constraint(phi["neg expl"])
                                neutral_form = e.compile().simplify()
                                phi["neutral"] = neutral_form

                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF, page 366
                # "if a" ensures that the action is not None (happens on the last step of a trace)
                a = token.step.action
                if a:
                    for phi in raw_fluent_factored:
                        clear_encoding(e)

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

                        # simplify/parse the formulas in phi before using them?
                        formula = (
                            (~precond[pos_pre_det] | phi["pos expl"])
                            & (~precond[neg_pre_det] | phi["neg expl"])
                            & phi["neutral"]
                        )
                        print(type(formula))
                        print(formula)
                        e.add_constraint(formula)
                        formula = e.compile().simplify()
                        phi["neutral"] = formula
                        clear_encoding(e)

                        e.add_constraint(
                            effects[pos_eff_det]
                            | (
                                neutrals[neut_det]
                                & ~precond[neg_pre_det]
                                & phi["pos expl"]
                            )
                        )
                        formula = e.compile().simplify()
                        print(formula)
                        phi["pos expl"] = formula
                        clear_encoding(e)

                        e.add_constraint(
                            effects[neg_eff_det]
                            | (
                                neutrals[neut_det]
                                & ~precond[pos_pre_det]
                                & phi["neg expl"]
                            )
                        )
                        formula = e.compile().simplify()
                        print(formula)
                        phi["neg expl"] = formula

                        # MOVE TO LATER
                        """
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
                        """
                if debug:
                    print("-" * 100)
                    if a:
                        print("\nAction taken: " + a.details() + "\n")
                    for obj in to_obs:
                        for phi in raw_fluent_factored:
                            f_str = phi["fluent"].details
                            if f_str == obj:
                                print("\nfluent: " + f_str)
                                print("\nexpl. for fluent being true:")
                                strings = list(
                                    Slaf.__print_nested_formula(
                                        phi["pos expl"].compile()
                                    )
                                )
                                strings.sort()
                                for s in strings:
                                    print(s)
                                print("\nexpl. for fluent being false:")
                                strings = list(
                                    Slaf.__print_nested_formula(
                                        phi["neg expl"].compile()
                                    )
                                )
                                strings.sort()
                                for s in strings:
                                    print(s)
                                print("\nexpl. for fluent being unaffected:")
                                strings = list(
                                    Slaf.__print_nested_formula(
                                        phi["neutral"].compile()
                                    )
                                )
                                strings.sort()
                                for s in strings:
                                    print(s)
                    print()
                    user_input = input("Hit enter to continue.")

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
