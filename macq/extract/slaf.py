import macq.extract as extract
from typing import Union, List, Set
from nnf import Var, Or, And, true, false

# from ..observation import Observation, PartialObservabilityToken
# from ..trace import Action, ObservationList
import bauhaus
from bauhaus import Encoding
from nnf import dsharp

from macq.observation import *
from macq.trace import *

e = Encoding()


class Slaf:
    # only need one true and one false
    top = true
    bottom = false

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
                phi["fluent"] = Var(f)
                phi["pos expl"] = {top}
                phi["neg expl"] = {top}
                phi["neutral"] = {top}
                raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def remove_subsumed_clauses(phi_form: Set):
        # print(phi_form)
        # print()
        to_del = set()
        # eliminate subsumed clauses
        for f in phi_form:
            for other in phi_form:
                if isinstance(f, Or) or isinstance(f, And):
                    f_set = {str(o) for o in f.children}
                else:
                    f_set = {str(f)}
                if not isinstance(other, Var):
                    other_set = {str(o) for o in other.children}
                    if f_set.issubset(other_set) and f_set != other_set and f != true:
                        to_del.add(other)
        for t in to_del:
            phi_form.discard(t)

    @staticmethod
    def or_refactor(maybe_lit):
        if isinstance(maybe_lit, Var):
            return Or([maybe_lit])
        else:
            return maybe_lit

    @staticmethod
    def as_strips_slaf(observations: ObservationList, debug: bool = False):
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
        top = Slaf.top
        bottom = Slaf.bottom
        global e
        validity_constraints = set()
        all_var = set()

        raw_fluent_factored = None
        # iterate through every observation in the list of observations/traces
        for obs in observations:
            # get the fluent factored formula for this observation/trace
            raw_fluent_factored = Slaf.__get_initial_fluent_factored(
                obs, raw_fluent_factored
            )
            if debug:
                all_f_details = [f["fluent"].name for f in raw_fluent_factored]
                all_f_details.sort()
                for f in all_f_details:
                    print(f)
                to_obs = []
                user_input = ""
                print(
                    "\nWhich fluents do you want to observe? Enter 'x' when you are finished.\n"
                )
                while user_input != "x":
                    user_input = input()
                    if user_input in all_f_details:
                        to_obs.append(user_input)
                        print(user_input + " added to the debugging list.")
                    else:
                        if user_input != "x":
                            print("The fluent you entered is invalid.")

            # iterate through all tokens (action/observation pairs) in this observation/trace
            for token in obs:
                if debug:
                    print("-" * 100)
                # steps 1. (d)-(e) of AS-STRIPS-SLAF
                all_o = [
                    Var(str(f)[1:-1]) if token.step.state[f] else ~Var(str(f)[1:-1])
                    for f in token.step.state.fluents
                ]
                for phi in raw_fluent_factored:
                    f = phi["fluent"]
                    # take account all of the current observations BEFORE the next action is taken.
                    for o in all_o:
                        # if this fluent is observed, update the formula accordingly.
                        # since we know the fluent is now true, the prior possible explanation for the fluent being true (involving past actions, etc) are now set to the neutral explanation; that is, one of those explanations has to be true in order for the prior action to have no effect on the fluent currently being true.
                        if f == o:
                            phi["neutral"].update(
                                [p.simplify() for p in phi["pos expl"]]
                            )
                            phi["pos expl"] = {top}
                            phi["neg expl"] = {bottom}
                            if debug and str(f) in to_obs:
                                print(
                                    f"{f} was observed to be true after the previous action was taken."
                                )
                        # the opposite happens if the fluent is observed to be false.
                        elif ~f == o:
                            phi["neutral"].update(
                                [n.simplify() for n in phi["neg expl"]]
                            )
                            phi["pos expl"] = {bottom}
                            phi["neg expl"] = {top}
                            if debug and str(f) in to_obs:
                                print(
                                    f"{f} was observed to be false after the previous action was taken."
                                )
                if debug:
                    print("Update according to observations.")
                    for obj in to_obs:
                        for phi in raw_fluent_factored:
                            f_str = phi["fluent"].name
                            if f_str == obj:
                                print("\nfluent: " + f_str)
                                print("\npossible expl. for fluent being true:")
                                for f in phi["pos expl"]:
                                    if f == top:
                                        print("true")
                                    elif f == bottom:
                                        print("false")
                                    else:
                                        e.pprint(f)
                                print("\npossible expl. for fluent being false:")
                                for f in phi["neg expl"]:
                                    if f == top:
                                        print("true")
                                    elif f == bottom:
                                        print("false")
                                    else:
                                        e.pprint(f)
                                print("\npossible expl. for fluent being unaffected:")
                                for f in phi["neutral"]:
                                    if f == top:
                                        print("true")
                                    elif f == bottom:
                                        print("false")
                                    else:
                                        e.pprint(f)
                    print()
                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF, page 366
                # "if a" ensures that the action is not None (happens on the last step of a trace)
                a = token.step.action
                if a:
                    for phi in raw_fluent_factored:
                        f = phi["fluent"]

                        pos_precond = Var(f"({f} is a precondition of {a.details()})")
                        neg_precond = Var(f"(~{f} is a precondition of {a.details()})")
                        pos_effect = Var(f"({a.details()} causes {f})")
                        neg_effect = Var(f"({a.details()} causes ~{f})")
                        neutral = Var(f"({a.details()} has no effect on {f})")

                        all_var.update(
                            [pos_precond, neg_precond, pos_effect, neg_effect, neutral]
                        )

                        all_phi_pos = [p.simplify() for p in phi["pos expl"]]
                        all_phi_neg = [n.simplify() for n in phi["neg expl"]]
                        all_phi_neut = [n.simplify() for n in phi["neutral"]]
                        phi["pos expl"] = set()
                        phi["neg expl"] = set()

                        phi["neutral"].update(
                            [(~pos_precond | p).simplify() for p in all_phi_pos]
                        )
                        phi["neutral"].update(
                            [(~neg_precond | n).simplify() for n in all_phi_neg]
                        )

                        phi["pos expl"].add(pos_effect | neutral)
                        phi["pos expl"].add(pos_effect | ~neg_precond)
                        phi["pos expl"].update(
                            [(pos_effect | p).simplify() for p in all_phi_pos]
                        )

                        phi["neg expl"].add(neg_effect | neutral)
                        phi["neg expl"].add(neg_effect | ~pos_precond)
                        phi["neg expl"].update(
                            [(neg_effect | n).simplify() for n in all_phi_neg]
                        )

                        validity_constraints.add(pos_effect | neg_effect | neutral)
                        validity_constraints.add((~pos_effect | ~neg_effect))
                        validity_constraints.add(~neg_effect | ~neutral)
                        validity_constraints.add(~pos_effect | ~neutral)
                        validity_constraints.add(~pos_precond | ~neg_precond)

                        # Slaf.remove_subsumed_clauses(phi["pos expl"])
                        # Slaf.remove_subsumed_clauses(phi["neg expl"])
                        # Slaf.remove_subsumed_clauses(phi["neutral"])

                if debug:
                    if a:
                        print("\nAction taken: " + a.details() + "\n")
                        for obj in to_obs:
                            for phi in raw_fluent_factored:
                                f_str = phi["fluent"].name
                                if f_str == obj:
                                    print("\nfluent: " + f_str)
                                    print(
                                        "\npossible expl. for fluent being true after "
                                        + a.details()
                                        + ":"
                                    )
                                    for f in phi["pos expl"]:
                                        if f == top:
                                            print("true")
                                        elif f == bottom:
                                            print("false")
                                        else:
                                            e.pprint(f)
                                    print(
                                        "\npossible expl. for fluent being false after "
                                        + a.details()
                                        + ":"
                                    )
                                    for f in phi["neg expl"]:
                                        if f == top:
                                            print("true")
                                        elif f == bottom:
                                            print("false")
                                        else:
                                            e.pprint(f)
                                    print(
                                        "\npossible expl. for fluent being unaffected after "
                                        + a.details()
                                        + ":"
                                    )
                                    for f in phi["neutral"]:
                                        if f == top:
                                            print("true")
                                        elif f == bottom:
                                            print("false")
                                        else:
                                            e.pprint(f)

                    print()

                    user_input = input("Hit enter to continue.")

        formula = set()
        # convert to formula once you have stepped through the whole observation/trace and applied all transformations
        # add as constraints to e here
        for phi in raw_fluent_factored:
            f = phi["fluent"]
            # convert to formula for each fluent
            all_phi_pos = [p.simplify() for p in phi["pos expl"]]
            all_phi_neg = [n.simplify() for n in phi["neg expl"]]
            all_phi_neut = [n.simplify() for n in phi["neutral"]]

            formula.update([(~f | p).simplify() for p in all_phi_pos])
            formula.update([(f | n).simplify() for n in all_phi_neg])
            formula.update([n for n in all_phi_neut])
        # formula.update(validity_constraints)

        full_formula = And({*[f.simplify() for f in formula]}).simplify()
        cnf_formula = And(map(Slaf.or_refactor, full_formula.children))

        # f = open("formula.txt", "w")
        # keys = list(cnf_formula)
        # keys = [str(f) for f in keys]
        # keys.sort()
        # for key in keys:
        #     f.write(str(key) + "\n")
        # f.close()

        ddnnf = dsharp.compile(
            cnf_formula, "/home/rebecca/macq/dsharp", extra_args=["-Fgraph", "out.dot"]
        )
        # print(ddnnf.size())
        children = set(cnf_formula.children)
        for f in all_var:
            # base_theory is the original CNF
            children.add(Or([~f]))
            check_theory = And(children)
            print(check_theory.is_CNF())
            # if False, then f is entailed
            if not check_theory.solve():
                print(f)
            children.discard(Or([~f]))


if __name__ == "__main__":
    from macq.extract import Extract, modes
    from macq.observation import (
        PartialObservabilityToken,
    )
    from macq.trace import *
    from macq.generate.pddl import VanillaSampling
    from pathlib import Path

    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=1)
    traces = vanilla.traces
    print(vanilla.problem.init)
    traces.print(wrap="y")

    observations = traces.tokenize(
        PartialObservabilityToken,
        method=PartialObservabilityToken.random_subset,
        percent_missing=0.3,
    )
    model = Extract(observations, modes.SLAF)

    print()
