import macq.extract as extract
from typing import Set, Union
from nnf import Var, Or, And, true, false, config
import bauhaus
from bauhaus import Encoding
from .model import Model
from ..observation import Observation, PartialObservabilityToken
from ..trace import Action, ObservationList

e = Encoding()


class Slaf:
    """Slaf model extraction method.

    Extracts a Model from state observations using the SLAF technique. The AS-STRIPS-SLAF
    algorithm is used to extract the effects of actions given a trace/observation. The algorithm
    is incapable of finding the preconditions of those actions, however.

    Note that SLAF learns partially observable, deterministic action models, and thus takes the
    PartialObservabilityToken type.

    The AS-STRIPS-SLAF algorithm works by defining "action propositions" for each action that define
    the possible preconditions, effects, or lack-thereof of that action and every possible fluent. A
    propositional formula is updated as each step is iterated through, and kept in a "fluent-factored form"
    that specifies the possible "explanations" behind each fluent being true, false, or unaffected. As actions
    are taken and states observed, these reasonings are updated and simplified. (Note that the pieces of the formula
    are stored carefully so as to easily conjoin them into one CNF formula later). Once all steps in the trace
    have been iterated through, the CNF formula is created, and all possible fluents/action propositions are
    iterated through to determine which ones are entailed. This information is then used to extract the Model.

    A debugging mode is supplied to help the user track any fluents they desire and to examine this fluent-
    factored form and its evolution through the steps.
    """

    # only need one true and one false
    top = true
    bottom = false

    def __new__(cls, o_list: ObservationList):
        """Creates a new Model object.

        Args:
            o_list (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if o_list.type is not PartialObservabilityToken:
            raise extract.IncompatibleObservationToken(o_list.type, Slaf)
        entailed = Slaf.__as_strips_slaf(o_list)
        # return the Model
        return Slaf.__sort_results(o_list, entailed)

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
        # get all the base fluents
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
        """Removes subsumed clauses to simplify the given formula.
        This is step 2. of AS-STRIPS-SLAF, however this step was taken as the formula was
        progressively created instead of once at the end, for efficiency purposes.

        Args:
            phi_form (Set):
                The set (conjunction) of formulas to simplify.
        """
        to_del = set()
        # if the overall phi formula (conjunction) has false, throw everything out
        if false in phi_form:
            phi_form.clear()
            return
        # eliminate subsumed clauses by comparing each formula with the others
        for f in phi_form:
            for other in phi_form:
                # simplify the formulas to sets of strings for comparison purposes
                if isinstance(f, Or) or isinstance(f, And):
                    f_set = {str(o) for o in f.children}
                else:
                    f_set = {str(f)}
                if not isinstance(other, Var):
                    other_set = {str(o) for o in other.children}
                    # if the subformula is a conjunction and has false in it, throw it out
                    if isinstance(other, And):
                        if "false" in other_set:
                            to_del.add(other)
                            break
                    # if the subformula is a disjunction and has true in it, throw it out
                    elif isinstance(other, Or):
                        if "true" in other_set:
                            to_del.add(other)
                            break
                    # otherwise, if the subformula can be represented by a smaller subformula, throw it out.
                    # also, "true" and "false" are empty sets, and unless we have one of the two cases above, we need to
                    # prevent them from throwing out formulas unnecessarily
                    if (
                        f_set.issubset(other_set)
                        and f_set != other_set
                        and f != true
                        and f != false
                    ):
                        to_del.add(other)
        # discard unnecessary formulas
        for t in to_del:
            phi_form.discard(t)

    @staticmethod
    def __or_refactor(maybe_lit: Union[Or, Var]):
        """Converts a "Var" fluent to an "Or" fluent.

        Args:
            maybe_lit (Union[Or, Var]):
                Fluent that is either type "Or" or "Var."

        Returns:
            A corresponding fluent of type "Or."
        """
        return Or([maybe_lit]) if isinstance(maybe_lit, Var) else maybe_lit

    @staticmethod
    def __sort_results(observations: ObservationList, entailed: Set):
        """Generates a `Model` given the set of entailed propositions.

        Args:
            observations (ObservationList):
                The observations supplied for extraction.
            entailed (Set)
                The set of propositions that were found to be entailed.

        Returns:
            The extracted `Model`.
        """
        learned_actions = {}
        base_fluents = {}
        model_fluents = set()
        # iterate through each step
        for o in observations.traces:
            for token in o:
                # if an action was taken on this step
                if token.step.action:
                    # set up a base LearnedAction with the known information
                    learned_actions[
                        token.step.action.details()
                    ] = extract.LearnedAction(
                        token.step.action.name,
                        token.step.action.obj_params,
                        cost=token.step.action.cost,
                    )
                # store all the possible fluents for later reference
                for f in token.step.state.fluents.keys():
                    base_fluents[str(f)[1:-1]] = f
        # iterate through all entailed propositions
        for e in entailed:
            precond = " is a precondition of "
            effect = " causes "
            neutral = " has no effect on "
            e = str(e)
            obj_params = set()
            # if this proposition holds information about a precondition
            if precond in e:
                # split to separate precondition and action, get rid of extra brackets
                info_split = e[1:-1].split(precond)
                precond = info_split[0]
                action = info_split[1]
                # update the precondition of this action with the appropriate fluent
                learned_actions[action].update_precond({base_fluents[precond]})
            # if this proposition holds information about an effect
            elif effect in e:
                # split to separate effect and action, get rid of extra brackets
                info_split = e[1:-1].split(effect)
                action = info_split[0]
                effect = info_split[1]
                # update either add or delete effects appropriately
                if "~" in effect:
                    # get rid of "~"
                    effect = effect[1:]
                    # update the delete effects of this action with the appropriate fluent
                    learned_actions[action].update_delete({base_fluents[effect]})
                else:
                    # update the add effects of this action with the appropriate fluent
                    learned_actions[action].update_add({base_fluents[effect]})
            else:
                # regular fluent (not an action proposition) is entailed
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
                NOTE: with the current implementation, SLAF only works with a single trace.

        Returns:
            The set of fluents that are entailed.
        """

        # ask the user if they want to run in debug mode
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

        global e
        top = Slaf.top
        bottom = Slaf.bottom
        validity_constraints = set()
        all_var = set()

        # get the fluent factored formula
        raw_fluent_factored = Slaf.__get_initial_fluent_factored(o_list)
        # get all base fluents to check entailments later
        all_var.update([phi["fluent"] for phi in raw_fluent_factored])
        # iterate through every observation
        for obs in o_list:
            # more options if the user is in debug mode
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
                """Steps 1. (d)-(e) of AS-STRIPS-SLAF.
                Steps (d)-(e) are done first as the action-observation order of SLAF is opposite to that of 
                how steps are stored in macq."""
                all_o = []
                # retrieve list of observations from the current state. Missing fluents are not taken into account.
                for f in token.step.state.fluents:
                    if token.step.state[f] != None:
                        if token.step.state[f]:
                            all_o.append(str(Var(str(f)[1:-1])))
                        else:
                            all_o.append(str(~Var(str(f)[1:-1])))

                """Iterate through every fluent in the fluent-factored transition belief formula and take 
                account of all of the current observations BEFORE the next action is taken.
                If this fluent is observed, update the formula accordingly.
                Since we know the fluent is now true, the prior possible explanation for the fluent being true 
                (involving past actions, etc) are now set to the neutral explanation; that is, one of those explanations 
                has to be true in order for the prior action to have no effect on the fluent currently being true.
                The opposite happens if the fluent is observed to be false.
                If the fluent is not observed to be either true or false (it is missing), then nothing happens."""
                for phi in raw_fluent_factored:
                    f = phi["fluent"]
                    if str(f) in all_o:
                        phi["neutral"].update([p.simplify() for p in phi["pos expl"]])
                        phi["pos expl"] = {top}
                        phi["neg expl"] = {bottom}
                        if debug and str(f) in to_obs:
                            print(
                                f"{f} was observed to be true after the previous action was taken."
                            )
                    elif str(~f) in all_o:
                        phi["neutral"].update([n.simplify() for n in phi["neg expl"]])
                        phi["pos expl"] = {bottom}
                        phi["neg expl"] = {top}
                        if debug and str(f) in to_obs:
                            print(
                                f"{f} was observed to be false after the previous action was taken."
                            )
                # display current updates
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

                """Steps 1. (a)-(c) of AS-STRIPS-SLAF.
                Creates new action propositions if necessary, as well as updates every fluent in the
                fluent-factored transition belief formula with information from the last step.
                Finally, validity constraints are added (section 5.2 of the SLAF paper) and the clauses are simplified
                (step 2 of the AS-STRIPS-SLAF algorithm).
                """
                a = token.step.action
                # ensures that the action is not None (happens on the last step of a trace)
                if a:
                    # iterate through every fluent in the fluent-factored transition belief formula
                    for phi in raw_fluent_factored:
                        f = phi["fluent"]

                        # create action propositions
                        pos_precond = Var(f"({f} is a precondition of {a.details()})")
                        neg_precond = Var(f"(~{f} is a precondition of {a.details()})")
                        pos_effect = Var(f"({a.details()} causes {f})")
                        neg_effect = Var(f"({a.details()} causes ~{f})")
                        neutral = Var(f"({a.details()} has no effect on {f})")

                        all_var.update(
                            [pos_precond, neg_precond, pos_effect, neg_effect, neutral]
                        )

                        # update the fluent-factored formula
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

                        # add validity constraints
                        validity_constraints.add(pos_effect | neg_effect | neutral)
                        validity_constraints.add((~pos_effect | ~neg_effect))
                        validity_constraints.add(~neg_effect | ~neutral)
                        validity_constraints.add(~pos_effect | ~neutral)
                        validity_constraints.add(~pos_precond | ~neg_precond)

                        # simplify each clause
                        Slaf.__remove_subsumed_clauses(phi["pos expl"])
                        Slaf.__remove_subsumed_clauses(phi["neg expl"])
                        Slaf.__remove_subsumed_clauses(phi["neutral"])
                # display current updates
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
        """Convert to formula once you have stepped through all observations and applied all transformations.
        NOTE: This would have to be refactored if the functionality for multiple traces was added, as each trace would 
        have to store its own separate formulas, and the conjunction would be taken at the end."""
        for phi in raw_fluent_factored:
            f = phi["fluent"]
            # convert to formula for each fluent
            all_phi_pos = [p.simplify() for p in phi["pos expl"]]
            all_phi_neg = [n.simplify() for n in phi["neg expl"]]
            all_phi_neut = [n.simplify() for n in phi["neutral"]]
            formula.update([(~f | p).simplify() for p in all_phi_pos])
            formula.update([(f | n).simplify() for n in all_phi_neg])
            formula.update([n for n in all_phi_neut])
        # add the validity constraints
        formula.update(validity_constraints)
        # create CNF formula
        full_formula = And({*[f.simplify() for f in formula]}).simplify()
        cnf_formula = And(map(Slaf.__or_refactor, full_formula.children))

        entailed = set()
        children = set(cnf_formula.children)
        # iterate through all fluents, gathering those that are entailed
        for f in all_var:
            children.add(Or([~f]))
            check_theory = And(children)
            # if False, then f is entailed
            with config(sat_backend="kissat"):
                if not check_theory.solve():
                    entailed.add(f)
            children.discard(Or([~f]))
        return entailed
