""".. include:: ../../docs/extract/slaf.md"""

from typing import Set, Union
from bauhaus import Encoding
from nnf import And, Or, Var, config, false, true
import macq.extract as extract
from ..observation import AtomicPartialObservation, ObservedTraceList
from .exceptions import IncompatibleObservationToken
from .learned_fluent import LearnedFluent
from .model import Model

# only used for pretty printing in debug mode
e = Encoding()


class SLAF:
    """SLAF model extraction method.

    Amir, E, and A Chang. 2008. “Learning Partially Observable Deterministic Action Models.”
    Journal of Artificial Intelligence Research 33: 349–402. https://doi.org/10.1613/jair.2575.

    Extracts a Model from state observations using the SLAF technique. The AS-STRIPS-SLAF
    algorithm is used to extract the effects of actions given a trace/observation. The algorithm
    is incapable of finding the preconditions of those actions, however.

    Note that SLAF learns partially observable, deterministic action models, and thus takes
    PartialObservation as the token type.

    The AS-STRIPS-SLAF algorithm works by defining "action propositions" for each action that define
    the possible preconditions, effects, or lack-thereof of that action and every possible fluent. A
    propositional formula is updated as each step is iterated through, and kept in a "fluent-factored form"
    that specifies the possible "explanations" behind each fluent being true, false, or unaffected. As actions
    are taken and states observed, these reasonings are updated and simplified. (Note that the pieces of the formula
    are stored carefully so as to easily conjoin them into one CNF formula later). Once all steps in the trace
    have been iterated through, the CNF formula is created, and all possible fluents/action propositions are
    iterated through to determine which ones are entailed. This information is then used to extract the Model.
    """

    # only need one true and one false
    top = true
    bottom = false

    def __new__(cls, o_list: ObservedTraceList, debug: bool = False, sample: bool = False):
        """Creates a new Model object.

        Args:
            o_list (ObservationList):
                The state observations to extract the model from.
            debug_mode (bool):
                An optional mode that helps the user track any fluents they desire by examining the evolution
                of their fluent-factored formulas through the steps.
            sample (bool):
                An optional mode that allows the user to sample the possible models instead of returning
                one that includes only guaranteed entailed fluents.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if o_list.type is not AtomicPartialObservation:
            raise IncompatibleObservationToken(o_list.type, SLAF)

        if len(o_list) != 1:
            raise Exception("The SLAF extraction technique only takes one trace.")

        SLAF.debug_mode = debug
        entailed = SLAF.__as_strips_slaf(o_list, sample)
        # return the Model
        return SLAF.__sort_results(o_list, entailed)

    @staticmethod
    def __get_initial_fluent_factored(o_list: ObservedTraceList):
        """Gets the initial fluent-factored formula of an observation/trace.

        Args:
            o_list (ObservationList):
                The observation list to extract the fluent-factored formula from.

        Returns:
            A list of dictionaries that holds the fluent-factored formula.
        """
        top = SLAF.top
        bottom = SLAF.bottom
        fluents = set()
        # get all the base fluents
        fluents.update([f for obs in o_list for token in obs for f in token.state])

        # set up the initial fluent factored form for the problem
        raw_fluent_factored = {}
        for f in fluents:
            phi = {}
            phi["fluent"] = Var(f)
            phi["pos expl"] = {top}
            phi["neg expl"] = {top}
            phi["neutral"] = {top}
            raw_fluent_factored[f] = phi
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
    def __sort_results(observations: ObservedTraceList, entailed: Set):
        """Generates a `Model` given the set of entailed propositions.

        Args:
            observations (ObservationLists):
                The observations supplied for extraction.
            entailed (Set)
                The set of propositions that were found to be entailed.

        Returns:
            The extracted `Model`.
        """
        learned_actions = {}
        model_fluents = observations.get_fluents()

        # iterate through each step
        for o in observations:
            for token in o:
                # if an action was taken on this step
                if token.action:
                    # set up a base LearnedAction with the known information
                    learned_actions[str(token.action)] = extract.LearnedAction(
                        token.action.name,
                        token.action.obj_params,
                        cost=token.action.cost,
                    )
        # iterate through all entailed propositions
        for e in entailed:
            precond = " is a precondition of "
            effect = " causes "
            neutral = " has no effect on "
            e = str(e)
            # if this proposition holds information about a precondition
            if precond in e:
                # split to separate precondition and action, get rid of extra brackets
                info_split = e[1:-1].split(precond)
                precond = info_split[0]
                action = info_split[1]
                # update the precondition of this action with the appropriate fluent
                #  only if it's a positive precondition
                if "~" not in precond:
                    learned_actions[action].update_precond({precond})
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
                    learned_actions[action].update_delete({effect})
                else:
                    # update the add effects of this action with the appropriate fluent
                    learned_actions[action].update_add({effect})
        return Model(model_fluents, set(learned_actions.values()))

    @staticmethod
    def __as_strips_slaf(o_list: ObservedTraceList, sample: bool):
        """Implements the AS-STRIPS-SLAF algorithm from section 5.3 of the SLAF paper.
        Iterates through the action/observation pairs of each observation/trace, returning
        a fluent-factored transition belief formula that filters according to that action/observation.
        The transition belief formulas for each trace/observation are conjoined to get one final formula,
        which is then solved using a SAT solver to extract models.

        Args:
            o_list (ObservationList):
                The list of observations/traces to apply the filtering algorithm to.
                NOTE: with the current implementation, SLAF only works with a single trace.

            sample (bool):
                If true, an arbitrary solution will be produced rather than just the entailed literals.

        Returns:
            The set of fluents that are entailed.
        """

        top = SLAF.top
        bottom = SLAF.bottom
        validity_constraints = set()
        all_var = set()
        debug_mode = SLAF.debug_mode

        # get the fluent factored formula
        raw_fluent_factored = SLAF.__get_initial_fluent_factored(o_list)
        # get all base fluents to check entailments later
        all_var.update([phi["fluent"] for phi in raw_fluent_factored.values()])
        # iterate through every observation
        for obs in o_list:
            # more options if the user is in debug mode
            if debug_mode:
                all_f_details = [f["fluent"].name for f in raw_fluent_factored.values()]
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
                if debug_mode:
                    print("-" * 100)

                all_o = []
                # retrieve list of observations from the current state. Missing fluents are not taken into account.
                for f in token.state:
                    if token.state[f] != None:
                        all_o.append(str(Var(f, token.state[f])))

                """Steps 1 (d)-(e) of AS-STRIPS-SLAF are taken care of in this loop.
                Note that steps (d)-(e) are done first as the action-observation order of SLAF is opposite to that of
                how steps are stored in macq.

                Iterate through every fluent in the fluent-factored transition belief formula and take
                account of all of the current observations BEFORE the next action is taken."""
                for phi in raw_fluent_factored.values():
                    f = phi["fluent"]
                    if str(f) in all_o:
                        """Step 1 (d): If this fluent is observed, update the formula accordingly.
                        Since we know the fluent is now true, the prior possible explanation for the fluent being true
                        (involving past actions, etc) are now set to the neutral explanation; that is, one of those explanations
                        has to be true in order for the prior action to have no effect on the fluent currently being true.
                        """
                        phi["neutral"].update([p.simplify() for p in phi["pos expl"]])
                        phi["pos expl"] = {top}
                        phi["neg expl"] = {bottom}
                        if debug_mode and str(f) in to_obs:
                            print(
                                f"{f} was observed to be true after the previous action was taken."
                            )

                    elif str(~f) in all_o:
                        """For Step 1 (e), the opposite happens if the fluent is observed to be false."""
                        phi["neutral"].update([n.simplify() for n in phi["neg expl"]])
                        phi["pos expl"] = {bottom}
                        phi["neg expl"] = {top}
                        if debug_mode and str(f) in to_obs:
                            print(
                                f"{f} was observed to be false after the previous action was taken."
                            )
                    """If the fluent is not observed to be either true or false (it is missing), then nothing happens."""
                # display current updates
                if debug_mode:
                    print("Update according to observations.")
                    for obj in to_obs:
                        f_str = raw_fluent_factored[obj]["fluent"].name
                        phi = raw_fluent_factored[f_str]
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

                """Steps 1. (a)-(c) and Step 2 of AS-STRIPS-SLAF are taken care of in this loop."""
                a = token.action
                # ensures that the action is not None (happens on the last step of a trace)
                if a:
                    # iterate through every fluent in the fluent-factored transition belief formula
                    for phi in raw_fluent_factored.values():
                        f = phi["fluent"]

                        # create action propositions
                        pos_precond = Var(f"({f} is a precondition of {a})")
                        neg_precond = Var(f"(~{f} is a precondition of {a})")
                        pos_effect = Var(f"({a} causes {f})")
                        neg_effect = Var(f"({a} causes ~{f})")
                        neutral = Var(f"({a} has no effect on {f})")

                        all_var.update(
                            [pos_precond, neg_precond, pos_effect, neg_effect, neutral]
                        )

                        # update the fluent-factored formula
                        all_phi_pos = [p.simplify() for p in phi["pos expl"]]
                        all_phi_neg = [n.simplify() for n in phi["neg expl"]]
                        all_phi_neut = [n.simplify() for n in phi["neutral"]]
                        phi["pos expl"] = set()
                        phi["neg expl"] = set()

                        """Steps 1 (a-c) - Update every fluent in the fluent-factored transition belief formula
                        with information from the last step."""

                        """Step 1 (a) - update the neutral effects."""
                        phi["neutral"].update(
                            [(~pos_precond | p).simplify() for p in all_phi_pos]
                        )
                        phi["neutral"].update(
                            [(~neg_precond | n).simplify() for n in all_phi_neg]
                        )

                        """Step 1 (b) - update the positive effects."""
                        phi["pos expl"].add(pos_effect | neutral)
                        phi["pos expl"].add(pos_effect | ~neg_precond)
                        phi["pos expl"].update(
                            [(pos_effect | p).simplify() for p in all_phi_pos]
                        )

                        """Step 1 (c) - update the negative effects."""
                        phi["neg expl"].add(neg_effect | neutral)
                        phi["neg expl"].add(neg_effect | ~pos_precond)
                        phi["neg expl"].update(
                            [(neg_effect | n).simplify() for n in all_phi_neg]
                        )

                        """add validity constraints (from section 5.2 of the SLAF paper)."""
                        validity_constraints.add(pos_effect | neg_effect | neutral)
                        validity_constraints.add((~pos_effect | ~neg_effect))
                        validity_constraints.add(~neg_effect | ~neutral)
                        validity_constraints.add(~pos_effect | ~neutral)
                        validity_constraints.add(~pos_precond | ~neg_precond)

                        """Step 2 - eliminate subsumed clauses in phi."""
                        SLAF.__remove_subsumed_clauses(phi["pos expl"])
                        SLAF.__remove_subsumed_clauses(phi["neg expl"])
                        SLAF.__remove_subsumed_clauses(phi["neutral"])
                # display current updates
                if debug_mode:
                    if a:
                        print("\nAction taken: " + str(a) + "\n")
                        for obj in to_obs:
                            f_str = raw_fluent_factored[obj]["fluent"].name
                            phi = raw_fluent_factored[f_str]
                            print("\nfluent: " + f_str)
                            print(
                                "\npossible expl. for fluent being true after "
                                + str(a)
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
                                + str(a)
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
                                + str(a)
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
                    user_input = input("Hit enter to continue.\n")

        formula = set()
        """Convert to formula once you have stepped through all observations and applied all transformations.
        NOTE: This would have to be refactored if the functionality for multiple traces was added, as each trace would
        have to store its own separate formulas, and the conjunction would be taken at the end."""
        for phi in raw_fluent_factored.values():
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
        cnf_formula = And(map(SLAF.__or_refactor, full_formula.children))

        entailed = set()
        if sample:
            with config(sat_backend="kissat"):
                sol = cnf_formula.solve()
                if sol:
                    for f in all_var:
                        if sol[str(f)]:
                            entailed.add(f)
        else:
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
