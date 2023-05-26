""".. include:: ../../docs/templates/extract/amdn.md"""

from macq.trace import Fluent, Action  # for typing
from macq.extract.learned_action import LearnedAction
from nnf.operators import implies

import macq.extract as extract
from typing import Dict, List, Optional, Union, Hashable
from nnf import Aux, Var, And, Or
from bauhaus import Encoding  # only used for pretty printing in debug mode
from .exceptions import (
    IncompatibleObservationToken,
)
from .model import Model
from ..trace import ActionPair
from ..observation import NoisyPartialDisorderedParallelObservation, ObservedTraceList
from ..utils.pysat import to_wcnf, extract_raw_model

e = Encoding


def pre(r: Fluent, act: Action):
    """Create a Var that enforces that the given fluent is a precondition of the given action.

    Args:
        r (Fluent):
            The precondition to be added.
        act (Action):
            The action that the precondition will be added to.
    Returns:
        The Var that enforces that the given fluent is a precondition of the given action.
    """
    return Var("(" + str(r)[1:-1] + " is a precondition of " + act.details() + ")")


def add(r: Fluent, act: Action):
    """Create a Var that enforces that the given fluent is an add effect of the given action.

    Args:
        r (Fluent):
            The add effect to be added.
        act (Action):
            The action that the add effect will be added to.
    Returns:
        The Var that enforces that the given fluent is an add effect of the given action.
    """
    return Var("(" + str(r)[1:-1] + " is added by " + act.details() + ")")


def delete(r: Fluent, act: Action):
    """Create a Var that enforces that the given fluent is a delete effect of the given action.

    Args:
        r (Fluent):
            The delete effect to be added.
        act (Action):
            The action that the delete effect will be added to.
    Returns:
        The Var that enforces that the given fluent is a delete effect of the given action.
    """
    return Var("(" + str(r)[1:-1] + " is deleted by " + act.details() + ")")


WMAX = 1


class AMDN:
    def __new__(
        cls,
        obs_tracelist: ObservedTraceList,
        debug: bool = False,
        occ_threshold: int = 1,
    ):
        """Creates a new Model object.

        Args:
            obs_tracelist (ObservationList):
                The state observations to extract the model from.
            debug (bool):
                Optional debugging mode.
            occ_threshold (int):
                Threshold to be used for noise constraints.

        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_tracelist.type is not NoisyPartialDisorderedParallelObservation:
            raise IncompatibleObservationToken(obs_tracelist.type, AMDN)

        return AMDN._amdn(obs_tracelist, debug, occ_threshold)

    @staticmethod
    def _amdn(obs_tracelist: ObservedTraceList, debug: bool, occ_threshold: int):
        """Main driver for the entire AMDN algorithm.
        The first line contains steps 1-4.
        The second line contains step 5.
        Finally, the final line corresponds to step 6 (return the model).

        Args:
            obs_tracelist (ObservationLists):
                The tokens to be fed into the algorithm.
            debug (bool):
                Optional debugging mode.
            occ_threshold (int):
                Threshold to be used for noise constraints.

        Returns:
            The extracted `Model`.
        """
        wcnf, decode = AMDN._solve_constraints(obs_tracelist, occ_threshold, debug)
        raw_model = extract_raw_model(wcnf, decode)
        return AMDN._extract_model(obs_tracelist, raw_model)

    @staticmethod
    def _or_refactor(maybe_lit: Union[Or, Var]):
        """Converts a "Var" fluent to an "Or" fluent.

        Args:
            maybe_lit (Union[Or, Var]):
                Fluent that is either type "Or" or "Var."

        Returns:
            A corresponding fluent of type "Or."
        """
        return Or([maybe_lit]) if isinstance(maybe_lit, Var) else maybe_lit

    @staticmethod
    def _extract_aux_set_weights(
        cnf_formula: And[Or[Var]], constraints: Dict, prob_disordered: float
    ):
        """Sets each clause in a CNF formula as a hard constraint, then sets any auxiliary variables to
        the appropriate weight detailed in the "Constraint DC" section of the AMDN paper.
        Used to help create disorder constraints.

        Args:
            cnf_formula (And[Or[Var]]):
                The CNF formula to extract the clauses and auxiliary variables from.
            constraints (Dict):
                The existing dictionary of disorder constraints.
            prob_disordered (float):
                The probability that the two actions relevant fot this constraint are disordered.
        """
        # find all the auxiliary variables
        for clause in cnf_formula.children:
            for var in clause.children:
                if isinstance(var.name, Aux) and var.true:
                    # aux variables are the soft clauses that get the original weight
                    constraints[AMDN._or_refactor(var)] = prob_disordered * WMAX
            # set each original constraint to be a hard clause
            constraints[clause] = "HARD"

    @staticmethod
    def _get_observe(obs_tracelist: ObservedTraceList):
        """Gets from the user which fluents they want to observe (for debug mode).

        Args:
            obs_tracelist (ObservationLists):
                The tokens that contain the fluents.

        Returns:
            A list of of which fluents the user wants to observe.
        """
        print("Select a proposition to observe:")
        sorted_f = [str(f) for f in obs_tracelist.propositions]
        sorted_f.sort()
        for f in sorted_f:
            print(f)
        to_obs = []
        user_input = ""
        while user_input != "x":
            user_input = input(
                "Which fluents do you want to observe? Enter 'x' when you are finished.\n"
            )
            if user_input in sorted_f:
                to_obs.append(user_input[1:-1])
                print(user_input + " added to the debugging list.")
            else:
                if user_input != "x":
                    print("The fluent you entered is invalid.")
        return to_obs

    @staticmethod
    def _debug_is_observed(constraint: Or, to_obs: List[str]):
        """Determines if the given constraint contains a fluent that is being observed in debug mode.

        Args:
            constraint (Or):
                The constraint to be analyzed.
            to_obs (List[str]):
                The list of fluents being observed.

        Returns:
            A bool that determines if the constraint should be observed or not.
        """
        for c in constraint.children:
            for v in to_obs:
                if v in str(c):
                    return True
        return False

    @staticmethod
    def _debug_simple_pprint(constraints: Dict, to_obs: List[str]):
        """Pretty print used for simple formulas in debug mode.

        Args:
            constraints (Dict):
                The constraints/weights to be pretty printed.
            to_obs (List[str]):
                The fluents being observed.
        """
        for c in constraints:
            observe = AMDN._debug_is_observed(c, to_obs)
            if observe:
                e.pprint(e, c)
                print(constraints[c])

    @staticmethod
    def _debug_aux_pprint(constraints: Dict, to_obs: List[str]):
        """Pretty print used for formulas with auxiliary variables in debug mode.

        Args:
            constraints (Dict):
                The constraints/weights to be pretty printed.
            to_obs (List[str]):
                The fluents being observed.
        """
        aux_map = {}
        index = 0
        for c in constraints:
            if AMDN._debug_is_observed(c, to_obs):
                for var in c.children:
                    if isinstance(var.name, Aux) and var.name not in aux_map:
                        aux_map[var.name] = f"aux {index}"
                        index += 1

        all_pretty_c = {}
        for c in constraints:
            if AMDN._debug_is_observed(c, to_obs):
                pretty_c = []
                for var in c.children:
                    if isinstance(var.name, Aux):
                        if var.true:
                            pretty_c.append(Var(aux_map[var.name]))
                            all_pretty_c[AMDN._or_refactor(var)] = Or(
                                [Var(aux_map[var.name])]
                            )
                        else:
                            pretty_c.append(~Var(aux_map[var.name]))
                    else:
                        pretty_c.append(var)
                # map disorder constraints to pretty disorder constraints
                all_pretty_c[c] = Or(pretty_c)

        for aux in aux_map.values():
            for c, v in all_pretty_c.items():
                for child in v.children:
                    if aux == child.name:
                        e.pprint(e, v)
                        print(constraints[c])
                        break
            print()

    @staticmethod
    def _build_disorder_constraints(obs_tracelist: ObservedTraceList):
        """Builds disorder constraints. Corresponds to step 1 of the AMDN algorithm.

        Args:
            obs_tracelist (ObservationLists):
                The tokens to be analyzed.

        Returns:
            The disorder constraints to be used in the algorithm.
        """
        disorder_constraints = {}

        # iterate through all traces
        for i in range(len(obs_tracelist.all_par_act_sets)):
            # get the parallel action sets for this trace
            par_act_sets = obs_tracelist.all_par_act_sets[i]
            # iterate through all pairs of parallel action sets for this trace
            # use -1 since we will be referencing the current parallel action set and the following one
            for j in range(len(par_act_sets) - 1):
                # for each action in psi_i+1
                for act_y in par_act_sets[j + 1]:
                    # for each action in psi_i
                    # NOTE: we do not use an existential here, as the paper describes (for each act_y in psi_i + 1,
                    # there exists an act_x in psi_i such that the condition holds.)
                    # this is due to the fact that the weights must be set for each action pair.
                    for act_x in par_act_sets[j]:
                        if act_x != act_y:
                            # calculate the probability of the actions being disordered (p)
                            p = obs_tracelist.probabilities[ActionPair({act_x, act_y})]
                            # each constraint only needs to hold for one proposition to be true
                            constraint_1 = []
                            constraint_2 = []
                            for r in obs_tracelist.propositions:
                                constraint_1.append(
                                    Or(
                                        [
                                            And(
                                                [
                                                    pre(r, act_x),
                                                    ~delete(r, act_x),
                                                    delete(r, act_y),
                                                ]
                                            ),
                                            And([add(r, act_x), pre(r, act_y)]),
                                            And([add(r, act_x), delete(r, act_y)]),
                                            And([delete(r, act_x), add(r, act_y)]),
                                        ]
                                    )
                                )
                                constraint_2.append(
                                    Or(
                                        [
                                            And(
                                                [
                                                    pre(r, act_y),
                                                    ~delete(r, act_y),
                                                    delete(r, act_x),
                                                ]
                                            ),
                                            And([add(r, act_y), pre(r, act_x)]),
                                            And([add(r, act_y), delete(r, act_x)]),
                                            And([delete(r, act_y), add(r, act_x)]),
                                        ]
                                    )
                                )
                            disjunct_all_constr_1 = Or(constraint_1).to_CNF()
                            disjunct_all_constr_2 = Or(constraint_2).to_CNF()
                            AMDN._extract_aux_set_weights(
                                disjunct_all_constr_1, disorder_constraints, (1 - p)
                            )
                            AMDN._extract_aux_set_weights(
                                disjunct_all_constr_2, disorder_constraints, p
                            )
        return disorder_constraints

    @staticmethod
    def _build_hard_parallel_constraints(obs_tracelist: ObservedTraceList):
        """Builds hard parallel constraints.

        Args:
            obs_tracelist (ObservationLists):
                The tokens to be analyzed.

        Returns:
            The hard parallel constraints to be used in the algorithm.
        """
        hard_constraints = {}
        # create a list of all <a, r> tuples
        for act in obs_tracelist.actions:
            for r in obs_tracelist.propositions:
                # for each action x proposition pair, enforce the two hard constraints with weight wmax
                hard_constraints[implies(add(r, act), ~pre(r, act))] = WMAX
                hard_constraints[implies(delete(r, act), pre(r, act))] = WMAX
        return hard_constraints

    @staticmethod
    def _build_soft_parallel_constraints(obs_tracelist: ObservedTraceList):
        """Builds soft parallel constraints.

        Args:
            obs_tracelist (ObservationLists):
                The tokens to be analyzed.

        Returns:
            The soft parallel constraints to be used in the algorithm.
        """
        soft_constraints = {}

        # NOTE: the paper does not take into account possible conflicts between the preconditions of actions
        # and the add/delete effects of other actions (similar to the hard constraints, but with other actions
        # in the parallel action set).

        # iterate through all traces
        for i in range(len(obs_tracelist.all_par_act_sets)):
            par_act_sets = obs_tracelist.all_par_act_sets[i]
            # iterate through all parallel action sets for this trace
            for j in range(len(par_act_sets)):
                # within each parallel action set, iterate through the same action set again to compare
                # each action to every other action in the set; setting constraints assuming actions are not disordered
                for act_x in par_act_sets[j]:
                    for act_x_prime in par_act_sets[j] - {act_x}:
                        p = obs_tracelist.probabilities[
                            ActionPair({act_x, act_x_prime})
                        ]
                        # iterate through all propositions
                        for r in obs_tracelist.propositions:
                            soft_constraints[
                                implies(add(r, act_x), ~delete(r, act_x_prime))
                            ] = (1 - p) * WMAX

        # iterate through all traces
        for i in range(len(obs_tracelist.all_par_act_sets)):
            par_act_sets = obs_tracelist.all_par_act_sets[i]
            # then, iterate through all pairs of parallel action sets for each trace
            for j in range(len(par_act_sets) - 1):
                # for each pair, compare every action in act_y to every action in act_x_prime; setting constraints assuming actions are disordered
                for act_y in par_act_sets[j + 1]:
                    for act_x_prime in par_act_sets[j] - {act_y}:
                        p = obs_tracelist.probabilities[
                            ActionPair({act_y, act_x_prime})
                        ]
                        # iterate through all propositions and similarly set the constraint
                        for r in obs_tracelist.propositions:
                            soft_constraints[
                                implies(add(r, act_y), ~delete(r, act_x_prime))
                            ] = (p * WMAX)

        return soft_constraints

    @staticmethod
    def _build_parallel_constraints(
        obs_tracelist: ObservedTraceList, debug: bool, to_obs: Optional[List[str]]
    ):
        """Main driver for building parallel constraints. Corresponds to step 2 of the AMDN algorithm.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            debug (bool):
                Optional debugging mode.
            to_obs (Optional[List[str]]):
                If in the optional debugging mode, the list of fluents to observe.

        Returns:
            The parallel constraints.
        """
        hard_constraints = AMDN._build_hard_parallel_constraints(obs_tracelist)
        soft_constraints = AMDN._build_soft_parallel_constraints(obs_tracelist)
        if debug:
            print("\nHard parallel constraints:")
            AMDN._debug_simple_pprint(hard_constraints, to_obs)
            print("\nSoft parallel constraints:")
            AMDN._debug_simple_pprint(soft_constraints, to_obs)
        return {**hard_constraints, **soft_constraints}

    @staticmethod
    def _calculate_all_r_occ(obs_tracelist: ObservedTraceList):
        """Calculates the total number of (true) propositions in the provided traces/tokens.

        Args:
            obs_tracelist (ObservationLists):
                The tokens to be analyzed.

        Returns:
            The total number of (true) propositions in the provided traces/tokens.
        """
        # tracks occurrences of all propositions
        all_occ = 0
        for trace in obs_tracelist:
            for step in trace:
                all_occ += len([f for f in step.state if step.state[f]])
        return all_occ

    @staticmethod
    def _set_up_occurrences_dict(obs_tracelist: ObservedTraceList):
        """Helper function used when constructing noise constraints.
        Sets up an "occurrence" dictionary used to track the occurrences of propositions
        before or after actions.

        Args:
            obs_tracelist (ObservationLists):
                The tokens to be analyzed.

        Returns:
            The blank "occurrences" dictionary.
        """
        # set up dict
        occurrences = {}
        for a in obs_tracelist.actions:
            occurrences[a] = {}
            for r in obs_tracelist.propositions:
                occurrences[a][r] = 0
        return occurrences

    @staticmethod
    def _noise_constraints_6(
        obs_tracelist: ObservedTraceList, all_occ: int, occ_threshold: int
    ):
        """Noise constraints (6) in the AMDN paper.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            all_occ (int):
                The number of occurrences of all (true) propositions in the given observation list.
            occ_threshold (int):
                Threshold to be used for noise constraints.

        Returns:
            The noise constraints.
        """
        noise_constraints_6 = {}
        occurrences = AMDN._set_up_occurrences_dict(obs_tracelist)

        # iterate over ALL the plan traces, adding occurrences accordingly
        for i in range(len(obs_tracelist)):
            # iterate through each step in each trace, omitting the last step because the last action is None/we access the state in the next step
            for j in range(len(obs_tracelist[i]) - 1):
                true_prop = [
                    f
                    for f in obs_tracelist[i][j + 1].state
                    if obs_tracelist[i][j + 1].state[f]
                ]
                for r in true_prop:
                    # count the number of occurrences of each action and its following proposition
                    occurrences[obs_tracelist[i][j].action][r] += 1

        # iterate through actions
        for a in occurrences:
            # iterate through all propositions for this action
            for r in occurrences[a]:
                occ_r = occurrences[a][r]
                # if the # of occurrences is higher than the user-provided threshold:
                if occ_r > occ_threshold:
                    # set constraint 6 with the calculated weight
                    noise_constraints_6[AMDN._or_refactor(~delete(r, a))] = (
                        occ_r / all_occ
                    ) * WMAX
        return noise_constraints_6

    @staticmethod
    def _noise_constraints_7(obs_tracelist: ObservedTraceList, all_occ: int):
        """Noise constraints (7) in the AMDN paper.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            all_occ (int):
                The number of occurrences of all (true) propositions in the given observation list.

        Returns:
            The noise constraints.
        """
        noise_constraints_7 = {}
        # set up dict
        occurrences = {}
        for r in obs_tracelist.propositions:
            occurrences[r] = 0

        for trace in obs_tracelist.all_states:
            for state in trace:
                true_prop = [r for r in state if state[r]]
                for r in true_prop:
                    occurrences[r] += 1

        # iterate through all traces
        for i in range(len(obs_tracelist.all_par_act_sets)):
            # get the next trace/states
            par_act_sets = obs_tracelist.all_par_act_sets[i]
            states = obs_tracelist.all_states[i]
            # iterate through all parallel action sets within the trace
            for j in range(len(par_act_sets)):
                # examine the states before and after each parallel action set; set constraints accordinglly
                true_prop = [r for r in states[j + 1] if states[j + 1][r]]
                for r in true_prop:
                    if not states[j][r]:
                        noise_constraints_7[
                            Or([add(r, act) for act in par_act_sets[j]])
                        ] = (occurrences[r] / all_occ) * WMAX
        return noise_constraints_7

    @staticmethod
    def _noise_constraints_8(obs_tracelist, all_occ: int, occ_threshold: int):
        """Noise constraints (8) in the AMDN paper.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            all_occ (int):
                The number of occurrences of all (true) propositions in the given observation list.
            occ_threshold (int):
                Threshold to be used for noise constraints.

        Returns:
            The noise constraints.
        """
        noise_constraints_8 = {}
        occurrences = AMDN._set_up_occurrences_dict(obs_tracelist)

        # iterate over ALL the plan traces, adding occurrences accordingly
        for i in range(len(obs_tracelist)):
            # iterate through each step in each trace
            for j in range(len(obs_tracelist[i])):
                # if the action is not None
                if obs_tracelist[i][j].action:
                    true_prop = [
                        f
                        for f in obs_tracelist[i][j].state
                        if obs_tracelist[i][j].state[f]
                    ]
                    for r in true_prop:
                        # count the number of occurrences of each action and its previous proposition
                        occurrences[obs_tracelist[i][j].action][r] += 1

        # iterate through actions
        for a in occurrences:
            # iterate through all propositions for this action
            for r in occurrences[a]:
                occ_r = occurrences[a][r]
                # if the # of occurrences is higher than the user-provided threshold:
                if occ_r > occ_threshold:
                    # set constraint 8 with the calculated weight
                    noise_constraints_8[AMDN._or_refactor(pre(r, a))] = (
                        occ_r / all_occ
                    ) * WMAX
        return noise_constraints_8

    @staticmethod
    def _build_noise_constraints(
        obs_tracelist: ObservedTraceList,
        occ_threshold: int,
        debug: bool,
        to_obs: Optional[List[str]],
    ):
        """Driver for building all noise constraints. Corresponds to step 3 of the AMDN algorithm.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            occ_threshold (int):
                Threshold to be used for noise constraints.
            debug (bool):
                Optional debugging mode.
            to_obs (Optional[List[str]]):
                If in the optional debugging mode, the list of fluents to observe.
        """
        # calculate all occurrences for use in weights
        all_occ = AMDN._calculate_all_r_occ(obs_tracelist)
        nc_6 = AMDN._noise_constraints_6(obs_tracelist, all_occ, occ_threshold)
        nc_7 = AMDN._noise_constraints_7(obs_tracelist, all_occ)
        nc_8 = AMDN._noise_constraints_8(obs_tracelist, all_occ, occ_threshold)
        if debug:
            print("\nNoise constraints 6:")
            AMDN._debug_simple_pprint(nc_6, to_obs)
            print("\nNoise constraints 7:")
            AMDN._debug_simple_pprint(nc_7, to_obs)
            print("\nNoise constraints 8:")
            AMDN._debug_simple_pprint(nc_8, to_obs)
        return {**nc_6, **nc_7, **nc_8}

    @staticmethod
    def _set_all_constraints(
        obs_tracelist: ObservedTraceList, occ_threshold: int, debug: bool
    ):
        """Main driver for generating all constraints in the AMDN algorithm.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            occ_threshold (int):
                Threshold to be used for noise constraints.
            debug (bool):
                Optional debugging mode.

        Returns:
            A dictionary that constains all of the constraints set and all of their weights.
        """
        to_obs = None
        if debug:
            to_obs = AMDN._get_observe(obs_tracelist)
        disorder_constraints = AMDN._build_disorder_constraints(obs_tracelist)
        if debug:
            print("\nDisorder constraints:")
            AMDN._debug_aux_pprint(disorder_constraints, to_obs)
        parallel_constraints = AMDN._build_parallel_constraints(
            obs_tracelist, debug, to_obs
        )
        noise_constraints = AMDN._build_noise_constraints(
            obs_tracelist, occ_threshold, debug, to_obs
        )
        return {**disorder_constraints, **parallel_constraints, **noise_constraints}

    @staticmethod
    def _solve_constraints(
        obs_tracelist: ObservedTraceList, occ_threshold: int, debug: bool
    ):
        """Returns the WCNF and the decoder according to the constraints generated.
        Corresponds to step 4 of the AMDN algorithm.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            occ_threshold (int):
                Threshold to be used for noise constraints.
            debug (bool):
                Optional debugging mode.

        Returns:
            The WCNF and corresponding decode dictionary.
        """
        constraints = AMDN._set_all_constraints(obs_tracelist, occ_threshold, debug)
        # extract hard constraints
        hard_constraints = []
        for c, weight in constraints.items():
            if weight == "HARD":
                hard_constraints.append(c)
        for c in hard_constraints:
            del constraints[c]

        wcnf, decode = to_wcnf(
            soft_clauses=And(constraints.keys()),
            hard_clauses=And(hard_constraints),
            weights=list(constraints.values()),
        )
        return wcnf, decode

    @staticmethod
    def _split_raw_fluent(raw_f: Hashable, learned_actions: Dict[str, LearnedAction]):
        """Helper function for `_extract_model` that updates takes raw fluents to update
        a dictionary of `LearnedActions`.

        Args:
            raw_f (Hashable):
                The raw fluent to parse.
            learned_actions (Dict[str, LearnedAction]):
                The dictionary of learned actions that will be used to create the model.
        """
        raw_f = str(raw_f)[1:-1]
        pre_str = " is a precondition of "
        add_str = " is added by "
        del_str = " is deleted by "
        if pre_str in raw_f:
            f, act = raw_f.split(pre_str)
            learned_actions[act].update_precond({f})
        elif add_str in raw_f:
            f, act = raw_f.split(add_str)
            learned_actions[act].update_add({f})
        else:
            f, act = raw_f.split(del_str)
            learned_actions[act].update_delete({f})

    @staticmethod
    def _extract_model(obs_tracelist: ObservedTraceList, model: Dict[Hashable, bool]):
        """Converts a raw model generated from the pysat module into a macq `Model`.
        Corresponds to step 5 of the AMDN algorithm.

        Args:
            obs_tracelist (ObservationLists):
                The tokens that were analyzed.
            model (Dict[Hashable, bool]):
                The raw model to parse and analyze.

        Returns:
            The macq action `Model`.
        """
        # convert the result to a Model
        fluents = obs_tracelist.propositions
        # set up LearnedActions
        learned_actions = {}
        for a in obs_tracelist.actions:
            # set up a base LearnedAction with the known information
            learned_actions[a.details()] = extract.LearnedAction(
                a.name, a.obj_params, cost=a.cost
            )
        # iterate through all fluents
        for raw_f in model:
            # update learned_actions (ignore auxiliary variables)
            if not isinstance(raw_f, Aux) and model[raw_f]:
                AMDN._split_raw_fluent(raw_f, learned_actions)
        # format
        actions = set(learned_actions.values())
        for act in actions:
            act.precond = {f"({p})" for p in act.precond}
            act.add = {f"({p})" for p in act.add}
            act.delete = {f"({p})" for p in act.delete}
        return Model(fluents, actions)
