from macq.extract.learned_action import LearnedAction
from nnf.operators import implies
import macq.extract as extract
from typing import Dict, Union, Set, Hashable
from nnf import Aux, Var, And, Or
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from .exceptions import (
    IncompatibleObservationToken,
    InvalidMaxSATModel,
)
from .model import Model
from ..trace import ObservationLists, ActionPair, Fluent # for typing
from ..observation import NoisyPartialDisorderedParallelObservation
from ..utils.pysat import to_wcnf, encode

def __set_precond(r, act):
    return Var(str(r)[1:-1] + " is a precondition of " + act.details())

def __set_add(r, act):
    return Var(str(r)[1:-1] + " is added by " + act.details())

def __set_del(r, act):
    return Var(str(r)[1:-1] + " is deleted by " + act.details())

# for easier reference
pre = __set_precond
add = __set_add
delete = __set_del

WMAX = 1

class AMDN:
    def __new__(cls, obs_lists: ObservationLists, occ_threshold: int):
        """Creates a new Model object.

        Args:
            obs_lists (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_lists.type is not NoisyPartialDisorderedParallelObservation:
            raise IncompatibleObservationToken(obs_lists.type, AMDN)

        return AMDN._amdn(obs_lists, occ_threshold)
    
    @staticmethod
    def _amdn(obs_lists: ObservationLists, occ_threshold: int):
        wcnf, decode = AMDN._solve_constraints(obs_lists, occ_threshold)
        raw_model = AMDN._extract_raw_model(wcnf, decode)
        return AMDN._extract_model(obs_lists, raw_model)

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
    def _extract_aux_set_weights(cnf_formula: And[Or[Var]], constraints: Dict, prob_disordered: float):
        aux_var = set()
        # find all the auxiliary variables
        for clause in cnf_formula.children:
            for var in clause.children:
                if isinstance(var.name, Aux):
                    aux_var.add(var.name)
            # set each original constraint to be a hard clause
            constraints[clause] = "HARD"
        # aux variables are the soft clauses that get the original weight
        for aux in aux_var:
            constraints[AMDN._or_refactor(Var(aux))] = prob_disordered * WMAX

    @staticmethod
    def _build_disorder_constraints(obs_lists: ObservationLists):
        disorder_constraints = {}
        # iterate through all traces
        for i in range(len(obs_lists.all_par_act_sets)):
            # get the parallel action sets for this trace
            par_act_sets = obs_lists.all_par_act_sets[i]
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
                            p = obs_lists.probabilities[ActionPair({act_x, act_y})]
                            # each constraint only needs to hold for one proposition to be true
                            constraint_1 = []
                            constraint_2 = []
                            for r in obs_lists.propositions:
                                constraint_1.append(Or([
                                    And([pre(r, act_x), ~delete(r, act_x), delete(r, act_y)]),
                                    And([add(r, act_x), pre(r, act_y)]),
                                    And([add(r, act_x), delete(r, act_y)]),
                                    And([delete(r, act_x), add(r, act_y)])
                                    ]).to_CNF())
                                constraint_2.append(Or([
                                    And([pre(r, act_y), ~delete(r, act_y), delete(r, act_x)]),
                                    And([add(r, act_y), pre(r, act_x)]),
                                    And([add(r, act_y), delete(r, act_x)]),
                                    And([delete(r, act_y), add(r, act_x)])
                                ]).to_CNF())
                            AMDN._extract_aux_set_weights(Or(constraint_1).to_CNF(), disorder_constraints, (1 - p))
                            AMDN._extract_aux_set_weights(Or(constraint_2).to_CNF(), disorder_constraints, p)
            return disorder_constraints

    @staticmethod
    def _build_hard_parallel_constraints(obs_lists: ObservationLists):
        hard_constraints = {}
        # create a list of all <a, r> tuples
        for act in obs_lists.actions:
            for r in obs_lists.propositions:
                # for each action x proposition pair, enforce the two hard constraints with weight wmax
                hard_constraints[implies(add(r, act), ~pre(r, act))] = WMAX
                hard_constraints[implies(delete(r, act), pre(r, act))] = WMAX
        return hard_constraints

    @staticmethod
    def _build_soft_parallel_constraints(obs_lists: ObservationLists):
        soft_constraints = {}

        # NOTE: the paper does not take into account possible conflicts between the preconditions of actions
        # and the add/delete effects of other actions (similar to the hard constraints, but with other actions
        # in the parallel action set).

        # iterate through all traces
        for i in range(len(obs_lists.all_par_act_sets)):
            par_act_sets = obs_lists.all_par_act_sets[i]
            # iterate through all parallel action sets for this trace
            for j in range(len(par_act_sets)):        
                # within each parallel action set, iterate through the same action set again to compare
                # each action to every other action in the set; setting constraints assuming actions are not disordered
                for act_x in par_act_sets[j]:
                    for act_x_prime in par_act_sets[j] - {act_x}:
                        p = obs_lists.probabilities[ActionPair({act_x, act_x_prime})]
                        # iterate through all propositions
                        for r in obs_lists.propositions:
                            soft_constraints[implies(add(r, act_x), ~delete(r, act_x_prime))] = (1 - p) * WMAX

        # iterate through all traces
        for i in range(len(obs_lists.all_par_act_sets)):
            par_act_sets = obs_lists.all_par_act_sets[i]
            # then, iterate through all pairs of parallel action sets for each trace
            for j in range(len(par_act_sets) - 1):
                # for each pair, compare every action in act_y to every action in act_x_prime; setting constraints assuming actions are disordered
                for act_y in par_act_sets[j + 1]:
                    for act_x_prime in par_act_sets[j] - {act_y}:
                        p = obs_lists.probabilities[ActionPair({act_y, act_x_prime})]
                        # iterate through all propositions and similarly set the constraint
                        for r in obs_lists.propositions:
                            soft_constraints[implies(add(r, act_y), ~delete(r, act_x_prime))] = p * WMAX
        return soft_constraints

    @staticmethod
    def _build_parallel_constraints(obs_lists: ObservationLists):
        return {**AMDN._build_hard_parallel_constraints(obs_lists), **AMDN._build_soft_parallel_constraints(obs_lists)}

    @staticmethod
    def _calculate_all_r_occ(obs_lists: ObservationLists):
        # tracks occurrences of all propositions
        all_occ = 0
        for trace in obs_lists:
            for step in trace:
                all_occ += len([f for f in step.state if step.state[f]])
        return all_occ

    @staticmethod
    def _set_up_occurrences_dict(obs_lists: ObservationLists):
        # set up dict
        occurrences = {}           
        for a in obs_lists.actions:
            occurrences[a] = {}
            for r in obs_lists.propositions:
                occurrences[a][r] = 0
        return occurrences
    
    @staticmethod
    def _noise_constraints_6(obs_lists: ObservationLists, all_occ: int, occ_threshold: int):
        noise_constraints_6 = {}
        occurrences = AMDN._set_up_occurrences_dict(obs_lists)

        # iterate over ALL the plan traces, adding occurrences accordingly
        for i in range(len(obs_lists)):
            # iterate through each step in each trace, omitting the last step because the last action is None/we access the state in the next step
            for j in range(len(obs_lists[i]) - 1):
                true_prop = [f for f in obs_lists[i][j + 1].state if obs_lists[i][j + 1].state[f]]
                for r in true_prop:
                    # count the number of occurrences of each action and its following proposition
                    occurrences[obs_lists[i][j].action][r] += 1

        # iterate through actions
        for a in occurrences:
            # iterate through all propositions for this action
            for r in occurrences[a]:
                occ_r = occurrences[a][r]
                # if the # of occurrences is higher than the user-provided threshold:
                if occ_r > occ_threshold:
                    # set constraint 6 with the calculated weight
                    noise_constraints_6[AMDN._or_refactor(~delete(r, a))] = (occ_r / all_occ) * WMAX
        return noise_constraints_6

    @staticmethod
    def _noise_constraints_7(obs_lists: ObservationLists, all_occ: int):
        noise_constraints_7 = {}
        # set up dict
        occurrences = {}           
        for r in obs_lists.propositions:
            occurrences[r] = 0

        for trace in obs_lists.all_states:
            for state in trace:
                true_prop = [r for r in state if state[r]]
                for r in true_prop:
                    occurrences[r] += 1

        # iterate through all traces
        for i in range(len(obs_lists.all_par_act_sets)):
            # get the next trace/states
            par_act_sets = obs_lists.all_par_act_sets[i]
            states = obs_lists.all_states[i]  
            # iterate through all parallel action sets within the trace
            for j in range(len(par_act_sets)):
                # examine the states before and after each parallel action set; set constraints accordinglly
                true_prop = [r for r in states[j + 1] if states[j + 1][r]]
                for r in true_prop:
                    if not states[j][r]:
                        noise_constraints_7[Or([add(r, act) for act in par_act_sets[j]])] = (occurrences[r]/all_occ) * WMAX
   
        return noise_constraints_7

    @staticmethod
    def _noise_constraints_8(obs_lists, all_occ: int, occ_threshold: int):
        noise_constraints_8 = {}
        occurrences = AMDN._set_up_occurrences_dict(obs_lists)

        # iterate over ALL the plan traces, adding occurrences accordingly
        for i in range(len(obs_lists)):
            # iterate through each step in each trace
            for j in range(len(obs_lists[i])):
                # if the action is not None
                if obs_lists[i][j].action:
                    true_prop = [f for f in obs_lists[i][j].state if obs_lists[i][j].state[f]]
                    for r in true_prop:
                        # count the number of occurrences of each action and its previous proposition
                        occurrences[obs_lists[i][j].action][r] += 1

        # iterate through actions
        for a in occurrences:
            # iterate through all propositions for this action
            for r in occurrences[a]:
                occ_r = occurrences[a][r]
                # if the # of occurrences is higher than the user-provided threshold:
                if occ_r > occ_threshold:
                    # set constraint 8 with the calculated weight
                    noise_constraints_8[AMDN._or_refactor(pre(r, a))] = (occ_r / all_occ) * WMAX
        return noise_constraints_8

    @staticmethod
    def _build_noise_constraints(obs_lists: ObservationLists, occ_threshold: int):
        # calculate all occurrences for use in weights
        all_occ = AMDN._calculate_all_r_occ(obs_lists)
        return{**AMDN._noise_constraints_6(obs_lists, all_occ, occ_threshold), **AMDN._noise_constraints_7(obs_lists, all_occ), **AMDN._noise_constraints_8(obs_lists, all_occ, occ_threshold)}

    @staticmethod
    def _set_all_constraints(obs_lists: ObservationLists, occ_threshold: int):
        return {**AMDN._build_disorder_constraints(obs_lists), **AMDN._build_parallel_constraints(obs_lists), **AMDN._build_noise_constraints(obs_lists, occ_threshold)}

    @staticmethod
    def _solve_constraints(obs_lists: ObservationLists, occ_threshold: int):
        constraints = AMDN._set_all_constraints(obs_lists, occ_threshold)
        # extract hard constraints
        hard_constraints = []
        for c, weight in constraints.items():
            if weight == "HARD":
                hard_constraints.append(c)
        
        for c in hard_constraints:
            del constraints[c]

        wcnf, decode = to_wcnf(soft_clauses=And(constraints.keys()), hard_clauses=And(hard_constraints), weights=list(constraints.values()))

        return wcnf, decode

    # TODO: move out to utils
    @staticmethod
    def _extract_raw_model(max_sat: WCNF, decode: Dict[int, Hashable]) -> Dict[Hashable, bool]:
        solver = RC2(max_sat)
        encoded_model = solver.compute()

        if not isinstance(encoded_model, list):
            # should never be reached
            raise InvalidMaxSATModel(encoded_model)

        # decode the model (back to nnf vars)
        model: Dict[Hashable, bool] = {
            decode[abs(clause)]: clause > 0 for clause in encoded_model
        }
        return model

    @staticmethod
    def _split_raw_fluent(raw_f: Hashable, learned_actions: Dict[str, LearnedAction]):
        raw_f = str(raw_f)
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
    def _extract_model(obs_lists: ObservationLists, model: Dict[Hashable, bool]):
        # convert the result to a Model
        fluents = obs_lists.propositions
        # set up LearnedActions
        learned_actions = {}
        for a in obs_lists.actions:
            # set up a base LearnedAction with the known information
            learned_actions[a.details()] = extract.LearnedAction(a.name, a.obj_params, cost=a.cost)            
        # iterate through all fluents
        for raw_f in model:
            # update learned_actions (ignore auxiliary variables)
            if not isinstance(raw_f, Aux):
                AMDN._split_raw_fluent(raw_f, learned_actions)

        return Model(fluents, learned_actions.values())