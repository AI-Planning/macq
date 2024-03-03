from pysat.formula import CNF
import macq
from macq.observation import ObservedTraceList
from macq.trace import Action, Fluent, State, PlanningObject
from macq.extract import model, LearnedLiftedAction
from macq.extract.learned_fluent import LearnedLiftedFluent, FullyHashedLearnedLiftedFluent
from itertools import product, chain, combinations
from pysat.solvers import Minisat22
solver = Minisat22()


class ESAMGenerator:
    obs_trace_list: ObservedTraceList
    L_bLA: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    # represents all parameter bound literals mapped by action
    literals = list[FullyHashedLearnedLiftedFluent] = list()
    literals2index: dict[FullyHashedLearnedLiftedFluent, int]
    preA: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    effA_add: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    effA_delete: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    #  add is 0 index in tuple and delete is
    # LiftedPreA, LiftedEFF both of them are stets of learned lifted fluents
    is_pre:  dict[str, set[FullyHashedLearnedLiftedFluent]]
    is_eff:  dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    Surely_eff: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    Surely_pre: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
    learned_lifted_fluents: set[LearnedLiftedFluent] = set()
    learned_lifted_action: set[LearnedLiftedAction] = set()
    action_2_sort: dict[str, list[str]] = dict()  # TODO use when knowing how to sort action

    def __init__(self, obs_trace_list: ObservedTraceList = None, action_2_sort: dict[str, list[str]] = None):
        """Creates a new SAM instance. if input includes sam_generator object than it uses the object provided
        instead of creating a new one
            Args:
                types set(str): a set of all types in the traces provided
                trace_list(TraceList): an object holding a
                    list of traces from the same domain. (macq.trace.trace_list.TraceList)
                action_2_sort(dict str -> list[str])

                                :return:
                                   a model based on SAM learning
                                """
        # step 0- initiate all class data structures.
        self.action_2_sort = action_2_sort
        self.obs_trace_list = obs_trace_list
        self.update_L_bLA()
        self.literals: list[FullyHashedLearnedLiftedFluent] = list(set().union(*self.L_bLA.values()))
        for index, l in enumerate(self.literals):
            self.literals2index[l] = index+1
        self.loop_over_actions()

    def update_L_bLA(self):
        """collects all parameter bound literals and maps them based on action name
                values of dict is a set[(fluent.name: str, sorts:list[str], param_inds:set[int])]"""
        actions_in_traces: set[Action] = self.obs_trace_list.get_actions()
        self.L_bLA = {name: set() for name in actions_in_traces.__getattribute__('name')}
        for f in self.obs_trace_list.get_fluents():  # for every fluent in the acts fluents
            for act in actions_in_traces:
                self.L_bLA[act.name].update(self.make_FullyHashedFluent_set(act, f))

    def make_FullyHashedFluent_set(self, action: Action, f: Fluent) -> set[FullyHashedLearnedLiftedFluent]:
        ret: set[FullyHashedLearnedLiftedFluent] = set()
        all_act_inds: list[list] = list(product(*find_indexes_in_l2(f.objects, action.obj_params)))
        sorts: list[str] = [self.action_2_sort[action.name].__getitem__(i) for i in all_act_inds[0]]
        if all(act_inds.__len__() > 0 for act_inds in all_act_inds):
            for act_inds in all_act_inds:  # for each product add the matching fluent information to the dict
                ret.add(FullyHashedLearnedLiftedFluent(f.name, sorts, act_inds))
        return ret

    def loop_over_actions(self):
        surely_effA_add: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
        # dict like preA that holds delete and add biding for each action
        # name
        surely_effA_delete: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
        # dict like preA that holds delete and add biding for each action name
        surely_preA: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()  # all fluents who are surely preconds
        conj_pre: dict[str, CNF] = dict()  # represents  parameter bound literals mapped by action, of pre-cond
        cnf_eff: dict[str, CNF] = dict()  # represents  parameter bound literals mapped by action, of pre-cond
        proxy_act_ind: int = 1  # counts action number, each action has different number, each proxy has additional info
        literal_2_index_in_eff: dict[int, list[list[int]]] = dict()  # lit num-> (clause index, index in clause)
        for lit in self.literals2index.values():  # to make unit propagation more efficient
            literal_2_index_in_eff[lit] = list()
            literal_2_index_in_eff[-lit] = list()
        lit_2_delete_from_clauses: dict[str, set[int]] = dict()  # will help us in the unit propagation
        for name in self.L_bLA.keys():  # init set for each name
            lit_2_delete_from_clauses[name] = set()

        def extract_clauses() -> (list[list[FullyHashedLearnedLiftedFluent]],
                                  list[list[FullyHashedLearnedLiftedFluent]]):
            self.obs_trace_list.get_all_transitions()
            for action, transitions in self.obs_trace_list.get_all_transitions().items():  # sas is state-action-state
                if isinstance(action, Action):
                    remove_redundant_preconditions(action, transitions)
                    make_cnf_eff(action, transitions)

            for action, transitions in self.obs_trace_list.get_all_transitions().items():
                for trans in transitions:
                    add_not_iseff(trans[1].state, action)
            for act_name in cnf_eff.keys():
                minimize(act_name)
            # minimize con_eff and continue

        def remove_redundant_preconditions(action: Action, transitions: list[list[macq.observation.Observation]]):
            """removes all parameter-bound literals that there groundings are not pre-state"""
            for trans in transitions:
                pre_state: State = trans[0].state
                to_remove: set[FullyHashedLearnedLiftedFluent] = set()
                for flu_inf in self.literals:
                    fluent = Fluent(flu_inf.name,
                                    [action.obj_params.__getitem__(ob_index) for ob_index in flu_inf.param_act_inds])
                    if (pre_state.fluents.keys().__contains__(fluent)) and not pre_state.fluents[fluent]:  # remove if
                        # unbound or if not true, means, preA contains at the end only true value fluents
                        to_remove.add(flu_inf)
                for flu_inf in to_remove:
                    conj_pre[action.name].clauses.remove([self.literals2index[flu_inf]])

        def make_cnf_eff(action: Action, transitions: list[list[macq.observation.Observation]]):
            """add all parameter-bound literals that are surely an effect"""
            for trans in transitions:
                pre_state: State = trans[0].state
                post_state: State = trans[1].state
                # add all add_effects of parameter bound literals
                add_literal_binding_to_eff(post_state, pre_state, action)

        def add_literal_binding_to_eff(pre_state: State, post_state: State, action: Action):

            negative_global_val = self.literals.__sizeof__()+1
            for k, v in pre_state.fluents.items():
                if not (post_state.keys().__contains__(k) and post_state.__getitem__(k) == v):
                    c_eff: list[int] = list()  # create clause for fluent
                    c_eff.append(-negative_global_val)
                    #  use the call below to get all know param act inds for fluents
                    fluents: set[FullyHashedLearnedLiftedFluent] = self.make_FullyHashedFluent_set(action, k)
                    # now we iterate over all observed bindings
                    for f in fluents:
                        if v:
                            c_eff.append(self.literals2index.get(f))  # its true therefore positive
                        else:
                            c_eff.append(-self.literals2index.get(f))  # its false therefore negative
                    cnf_eff[action.name].append(clause=c_eff)  # add clause to actions effects

        def add_not_iseff(post_state: State, action: Action):
            # TODO support to understand how add and delete effects
            # TODO handle this situation, suppose ut was false and became true, then -l is not in post state
            # TODO conclusion is to differ negative and positive fluents when handling this event!
            for f in self.literals:
                fluent = Fluent(f.name, [action.obj_params[index] for index in f.param_act_inds])
                if post_state.fluents.__contains__(fluent):
                    if not post_state.fluents[fluent]:
                        lit_2_delete_from_clauses[action.name].add(self.literals2index[f])
                    else:
                        lit_2_delete_from_clauses[action.name].add(-self.literals2index[f])
                else:
                    lit_2_delete_from_clauses[action.name].add(-self.literals2index[f])

        def remove_subsumed_clauses(action_name: str):
            pass

        def minimize(action_name: str):
            # unit propagation to minimize -iseff(l)
            for clause in cnf_eff[action_name].clauses:
                if isinstance(clause, list):
                    for index, literal in list(enumerate(reversed(clause))):
                        if lit_2_delete_from_clauses[action_name].__contains__(literal):
                            clause.pop(index)
            remove_subsumed_clauses(action_name)

        def delete_unit_clauses(cnf: CNF):
            """ removes all clauses of size 1  meant to be used after assigning surely_pre/eff all size 1 literals"""
            for index, clause in reversed(list(enumerate(cnf.clauses))):
                if len(clause) == 1:
                    cnf.clauses.pop(index)

        def get_unit_clauses_eff(formula: CNF)\
                -> (set[FullyHashedLearnedLiftedFluent], set[FullyHashedLearnedLiftedFluent]):
            """process all actions cnf effects, and returns tuple of unit clauses s.t <set[add_f],set[delete_f]>
            where add_f is fluents that has an add effect and delete_f is fluents that have del effect"""
            add_unit_clauses_in_fluent_rep: set[FullyHashedLearnedLiftedFluent] = set()
            delete_unit_clauses_in_fluent_rep: set[FullyHashedLearnedLiftedFluent] = set()
            for clause in formula.clauses:
                if clause.__sizeof__ == 1:
                    if clause[0] > 0:
                        add_unit_clauses_in_fluent_rep.add(self.literals[abs(clause[0])])
                    else:
                        delete_unit_clauses_in_fluent_rep.add(self.literals[abs(clause[0])])
            return add_unit_clauses_in_fluent_rep, delete_unit_clauses_in_fluent_rep

        def create_proxy_actions(action: str, act_num: int):
            # TODO understand the choosing of set S powerset to construct a proxy action
            proxy_index = 1
            delete_unit_clauses(cnf_eff[action])
            all_S_comb: list[tuple] = list()
            all_subsets: list = list()
            for sublist in cnf_eff[action].clauses:
                subsets = chain.from_iterable(combinations(sublist, r) for r in range(1, len(sublist) + 1))
                all_subsets.append(list(subsets))
            all_S_comb = list(product(*all_subsets))
            for S in all_S_comb:
                prox_act_name: str = str(action+f"{action}{act_num}.{proxy_index}")
                # eff(AS) ←SurelyEff
                ef_delete: set[FullyHashedLearnedLiftedFluent] = surely_effA_delete[act]  # eff(AS) ←SurelyEff
                ef_add: set[FullyHashedLearnedLiftedFluent] = surely_effA_add[act]  # eff(AS) ←SurelyEff
                pre: set[FullyHashedLearnedLiftedFluent] = surely_preA[act]  # pre(AS) ←SurelyPre;
                # we need to do set difference therefore we will convert S from list of tuples to a set of lists
                S_as_clauses: set[list[int]] = {list(map(self.literals2index.get, sublist)) for sublist in S}
                for cl in set(cnf_eff[act].clauses).difference(S_as_clauses):
                    # pre.add() add all l in cl to pre
                    pass
                proxy_index += 1  # increase proxy action index

        # main algorithm!!!

        for act in self.L_bLA.keys():
            for lit in self.literals2index.values():
                conj_pre[act].append(lit)
        extract_clauses()

        for act in self.L_bLA.keys():  # add unit clauses to add and delete effects
            surely_effA_add[act], surely_effA_delete[act] = get_unit_clauses_eff(cnf_eff[act])
            surely_preA[act] = set([self.literals[abs(index) + 1] for clause in conj_pre[act].clauses for index in
                                    clause])
            # add preconditions!
        # TODO create proxy actions!
            create_proxy_actions(act, proxy_act_ind)
            proxy_act_ind += 1


def find_indexes_in_l2(l1: list[PlanningObject], l2: list[PlanningObject]) -> (list[list[PlanningObject]]):
    index_dict = {}

    # Build a dictionary with elements of l2 and their indexes
    for index, element in enumerate(l2):
        if element not in index_dict:
            index_dict[element] = [index]
        else:
            index_dict[element].append(index)

    # Find indexes in l2 for each element in l1
    result = []
    for element in l1:
        if element in index_dict:
            result.append(index_dict[element])
        else:
            # Element not found in l2
            result.append([])

    return result
