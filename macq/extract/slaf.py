import macq.extract as extract
from typing import Union, List, Set, Dict
from nnf import Var, Or, And, true, false
from ..observation import Observation, PartialObservabilityToken
from .model import Model
from ..trace import Action, ObservationList, Fluent
import bauhaus
from bauhaus import Encoding
from nnf import dsharp


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
        entailed = Slaf.__as_strips_slaf(observations)
        return Slaf.__sort_results(observations, entailed)

    @staticmethod
    def __get_initial_fluent_factored(o_list: ObservationList):
        """Gets the initial fluent-factored formula of an observation/trace.

        Args:
            o_list (ObservationList):
                The observation list to extract the fluent-factored formula from.

        Returns:
            A list of dictionaries that holds the fluent-factored formula.
        """
        top = Slaf.top
        bottom = Slaf.bottom
        fluents = set()

        fluents.update(
            [f for obs in o_list for token in obs for f in token.get_all_base_fluents()]
        )

        # set up the initial fluent factored form for the problem
        raw_fluent_factored = []
        for f in fluents:
            phi = {}
            phi["fluent"] = Var(f)
            phi["pos expl"] = {top}
            phi["neg expl"] = {top}
            phi["neutral"] = {top}
            raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def __remove_subsumed_clauses(phi_form: Set):
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
    def __or_refactor(maybe_lit):
        if isinstance(maybe_lit, Var):
            return Or([maybe_lit])
        else:
            return maybe_lit

    @staticmethod
    def __sort_results(observations: ObservationList, entailed: Set):
        learned_actions = {}
        base_fluents = {}
        model_fluents = set()
        for o in observations.traces:
            for token in o:
                if token.step.action:
                    learned_actions[
                        token.step.action.details()
                    ] = extract.LearnedAction(
                        token.step.action.name,
                        token.step.action.obj_params,
                        cost=token.step.action.cost,
                    )
                for f in token.step.state.fluents.keys():
                    base_fluents[str(f)[1:-1]] = f
        for e in entailed:
            precond = " is a precondition of "
            effect = " causes "
            neutral = " has no effect on "
            e = str(e)
            obj_params = set()
            if precond in e:
                # split to separate precondition and action, get rid of extra brackets
                info_split = e[1:-1].split(precond)
                precond = info_split[0]
                action = info_split[1]
                learned_actions[action].update_precond({base_fluents[precond]})
            elif effect in e:
                # split to separate effect and action, get rid of extra brackets
                info_split = e[1:-1].split(effect)
                action = info_split[0]
                effect = info_split[1]
                # update either add or delete effects appropriately
                if "~" in effect:
                    # get rid of "~"
                    effect = effect[1:]
                    learned_actions[action].update_delete({base_fluents[effect]})
                else:
                    learned_actions[action].update_add({base_fluents[effect]})
            else:
                # regular fluent
                if not neutral in e:
                    model_fluents.add(e)
        return Model(model_fluents, set(learned_actions.values()))

    @staticmethod
    def __as_strips_slaf(o_list: ObservationList):
        """Implements the AS-STRIPS-SLAF algorithm from section 5.3 of the SLAF paper.
        Iterates through the action/observation pairs of each observation/trace, returning
        a fluent-factored transition belief formula that filters according to that action/observation.
        The transition belief formulas for each trace/observation are conjoined to get one final formula,
        which is then solved using a SAT solver to extract models.

        Args:
            o_list (ObservationList):
                The list of observations/traces to apply the filtering algorithm to.
        """

        inputOK = False
        while not inputOK:
            inputOK = True
            user_input = input(
                "Do you want to run the algorithm in debug mode, where you can track the progression of individual fluents? (y/n)"
            )
            if user_input == "y":
                debug = True
                print("\nRunning in debug mode...\n")
            elif user_input == "n":
                debug = False
                print("\nRunning normally...\n")
            else:
                inputOK = False
                print("Invalid input.")

        # get global variables
        top = Slaf.top
        bottom = Slaf.bottom
        global e
        validity_constraints = set()
        all_var = set()

        # get the fluent factored formula
        raw_fluent_factored = Slaf.__get_initial_fluent_factored(o_list)
        # iterate through every observation in the list of observations/traces
        for obs in o_list:
            if debug:
                all_f_details = [f["fluent"].name for f in raw_fluent_factored]
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
                if debug:
                    print("-" * 100)
                # steps 1. (d)-(e) of AS-STRIPS-SLAF
                all_o = [
                    str(Var(str(f)[1:-1]))
                    if token.step.state[f]
                    else str(~Var(str(f)[1:-1]))
                    for f in token.step.state.fluents
                ]
                for phi in raw_fluent_factored:
                    f = phi["fluent"]
                    """take account all of the current observations BEFORE the next action is taken.
                    if this fluent is observed, update the formula accordingly.
                    since we know the fluent is now true, the prior possible explanation for the fluent being true 
                    (involving past actions, etc) are now set to the neutral explanation; that is, one of those explanations 
                    has to be true in order for the prior action to have no effect on the fluent currently being true. """
                    if str(f) in all_o:
                        phi["neutral"].update([p.simplify() for p in phi["pos expl"]])
                        phi["pos expl"] = {top}
                        phi["neg expl"] = {bottom}
                        if debug and str(f) in to_obs:
                            print(
                                f"{f} was observed to be true after the previous action was taken."
                            )
                    # the opposite happens if the fluent is observed to be false.
                    elif str(~f) in all_o:
                        phi["neutral"].update([n.simplify() for n in phi["neg expl"]])
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

                        Slaf.__remove_subsumed_clauses(phi["pos expl"])
                        Slaf.__remove_subsumed_clauses(phi["neg expl"])
                        Slaf.__remove_subsumed_clauses(phi["neutral"])

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
        for phi in raw_fluent_factored:
            f = phi["fluent"]
            # convert to formula for each fluent
            all_phi_pos = [p.simplify() for p in phi["pos expl"]]
            all_phi_neg = [n.simplify() for n in phi["neg expl"]]
            all_phi_neut = [n.simplify() for n in phi["neutral"]]

            formula.update([(~f | p).simplify() for p in all_phi_pos])
            formula.update([(f | n).simplify() for n in all_phi_neg])
            formula.update([n for n in all_phi_neut])
        formula.update(validity_constraints)

        full_formula = And({*[f.simplify() for f in formula]}).simplify()
        cnf_formula = And(map(Slaf.__or_refactor, full_formula.children))

        ddnnf = dsharp.compile(
            cnf_formula, "/home/rebecca/macq/dsharp", extra_args=["-Fgraph", "out.dot"]
        )
        entailed = set()
        # print(ddnnf.size())
        children = set(cnf_formula.children)
        count = 0
        for f in all_var:
            count += 1
            print(str(count) + "/" + str(len(all_var)))
            # base_theory is the original CNF
            children.add(Or([~f]))
            check_theory = And(children)
            # print(check_theory.is_CNF())
            # if False, then f is entailed
            if not check_theory.solve():
                entailed.add(f)
            children.discard(Or([~f]))
        return entailed
