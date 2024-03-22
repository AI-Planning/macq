from macq.observation import ObservedTraceList
from macq.observation.observation import Observation
from macq.trace import Action, Fluent, State, PlanningObject
from macq.extract import LearnedLiftedAction
from macq.extract.learned_fluent import LearnedLiftedFluent, FullyHashedLearnedLiftedFluent
from itertools import product, chain, combinations


class ESAMGenerator:

    def __new__(cls, obs_trace_list: ObservedTraceList = None, action_2_sort: dict[str, list[str]] = None):
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
        literals2index: dict[FullyHashedLearnedLiftedFluent, int] = dict()
        literals = list[FullyHashedLearnedLiftedFluent] = list()

        def make_FullyHashedFluent_set(acton: Action, flu: Fluent) -> set[FullyHashedLearnedLiftedFluent]:
            ret: set[FullyHashedLearnedLiftedFluent] = set()
            all_act_inds: list[list] = list(product(*find_indexes_in_l2(flu.objects, acton.obj_params)))
            sorts: list[str] = [action_2_sort[acton.name].__getitem__(i) for i in all_act_inds[0]]
            if all(act_inds.__len__() > 0 for act_inds in all_act_inds):
                for act_inds in all_act_inds:  # for each product add the matching fluent information to the dict
                    ret.add(FullyHashedLearnedLiftedFluent(flu.name, sorts, act_inds))
            return ret

        actions_in_traces: set[Action] = obs_trace_list.get_actions()
        # step 1, collect all literals binding of each action
        L_bLA: dict[str, set[FullyHashedLearnedLiftedFluent]] = {
            act.name: set() for act in actions_in_traces.__getattribute__('name')}
        for f in obs_trace_list.get_fluents():  # for every fluent in the acts fluents
            for act in actions_in_traces:
                L_bLA[act.name].update(make_FullyHashedFluent_set(act, f))

        literals: list[FullyHashedLearnedLiftedFluent] = list(set().union(*L_bLA.values()))
        for index, l in enumerate(literals):
            literals2index[l] = index+1

        conj_pre: dict[str, set[int]] = dict()  # represents parameter bound literals mapped by action, of pre-cond
        cnf_eff_add: dict[str, set[set[int]]] = dict()  # represents parameter bound literals mapped by action, of eff
        cnf_eff_del: dict[str, set[set[int]]] = dict()  # represents parameter bound literals mapped by action, of eff
        lit_2_delete_from_clauses: dict[str, set[int]] = dict()  # will help us in the unit propagation""

        for name in [a.name for a in actions_in_traces]:  # init set for each name
            conj_pre[name] = {literals2index[literal] for literal in literals}
            lit_2_delete_from_clauses[name] = set()
            cnf_eff_add[name] = set()
            cnf_eff_del[name] = set()

        def extract_clauses() -> (list[list[FullyHashedLearnedLiftedFluent]],
                                  list[list[FullyHashedLearnedLiftedFluent]]):
            def remove_redundant_preconditions():
                """removes all parameter-bound literals that there groundings are not pre-state"""
                for tr in transitions:
                    pre_state: State = tr[0].state
                    for flu_inf in literals:
                        fluent = Fluent(flu_inf.name,
                                        [a.obj_params.__getitem__(ob_index) for ob_index in flu_inf.param_act_inds])
                        if (fluent in pre_state.fluents.keys()) and not pre_state.fluents[fluent]:  # remove if
                            # unbound or if not true, means, preA contains at the end only true value fluents
                            conj_pre[a.name].remove(literals2index[flu_inf])

            def make_cnf_eff():
                """add all parameter-bound literals that are surely an effect"""
                for tr in transitions:
                    pre_state: State = tr[0].state
                    post_state: State = tr[1].state
                    # add all add_effects of parameter bound literals
                    for k, v in pre_state.fluents.items():
                        if k not in post_state.keys() or post_state[k] != v:
                            c_eff: set[int] = set()  # create clause for fluent
                            #  use the call below to get all know param act inds for fluents
                            fluents: set[FullyHashedLearnedLiftedFluent] = make_FullyHashedFluent_set(a, k)
                            # now we iterate over all observed bindings
                            for flu in fluents:
                                if v:
                                    # its true therefore positive
                                    c_eff.add(literals2index.get(flu))
                                else:
                                    # its false therefore negative
                                    c_eff.add(literals2index.get(flu))
                            if v and len(c_eff) > 0:
                                # was true in pre-state and in post state is false -> remove effect
                                cnf_eff_del[a.name].add(c_eff)
                            elif len(c_eff) > 0:
                                # was true in pre-state and in post state is false -> remove effect
                                cnf_eff_add[a.name].add(c_eff)
            for a, transitions in obs_trace_list.get_all_transitions().items():  # sas is state-action-state
                if isinstance(a, Action):
                    remove_redundant_preconditions()
                    make_cnf_eff()

            remove_from_add_eff: dict[str, set[int]] = dict()  # add effects that needs to be removed(not eff)
            remove_from_del_eff: dict[str, set[int]] = dict()  # delete effects that needs to be removed(not eff)

            def add_not_iseff(post_state: State):
                for flu in literals:
                    fluent = Fluent(f.name, [a.obj_params[ind] for ind in flu.param_act_inds])
                    if fluent in post_state.fluents:
                        if not post_state.fluents[fluent]:  # flu is not in post state so flu is not an add effect
                            remove_from_add_eff[a.name].add(literals2index[flu])
                        else:  # flu is in post state so remove flu is not a del effect
                            remove_from_del_eff[a.name].add(literals2index[flu])
                    else:
                        remove_from_del_eff[a.name].add(literals2index[flu])
            for a, transitions in obs_trace_list.get_all_transitions().items():
                for trans in transitions:
                    add_not_iseff(trans[1].state)  # trans[1].state is the post state

            # removing all not iseff that need to be removed
            for act_name in [a.name for a in actions_in_traces]:
                for lit_to_remove in remove_from_add_eff[act_name]:
                    for clause in cnf_eff_add[act_name]:
                        clause.remove(lit_to_remove)
                for lit_to_remove in remove_from_del_eff[act_name]:
                    for clause in cnf_eff_del[act_name]:
                        clause.remove(lit_to_remove)

            def minimize(cnf: set[set[int]]):
                pass  # TODO implement
            for act_name in [a.name for a in actions_in_traces]:
                minimize(cnf_eff_add[act_name])
                minimize(cnf_eff_del[act_name])
            # minimize con_eff and continue

        def get_and_delete_unit_clauses_eff(act_name)\
                -> (set[FullyHashedLearnedLiftedFluent], set[FullyHashedLearnedLiftedFluent]):
            """process all actions cnf effects, and returns tuple of unit clauses s.t <set[add_f],set[delete_f]>
            where add_f is fluents that has an add effect and delete_f is fluents that have del effect"""
            add_unit_clauses_in_fluent_rep: set[FullyHashedLearnedLiftedFluent] = set()
            delete_unit_clauses_in_fluent_rep: set[FullyHashedLearnedLiftedFluent] = set()
            to_remove_del: set[set[int]] = set()
            to_remove_add: set[set[int]] = set()
            for clause in cnf_eff_add[act_name]:
                if len(clause) == 1:
                    add_unit_clauses_in_fluent_rep.add(literals[abs(clause.copy().pop())])
                    to_remove_add.add(clause)
            for clause in cnf_eff_del[act_name]:
                if len(clause) == 1:
                    add_unit_clauses_in_fluent_rep.add(literals[abs(clause.copy().pop())])
                    to_remove_del.add(clause)
            cnf_eff_add[act_name].difference_update(to_remove_add)
            cnf_eff_del[act_name].difference_update(to_remove_del)

            return add_unit_clauses_in_fluent_rep, delete_unit_clauses_in_fluent_rep

        proxy_act_ind: int = 1  # counts action number, each action has different number, each proxy has extra info

        def create_proxy_actions(act_name: str, act_num: int):
            # TODO FIX this to fit sympy
            # TODO understand the choosing of set S powerset to construct a proxy action
            pass
            '''
            proxy_index = 1
            delete_unit_clauses(act_name)
            all_S_comb: list[tuple] = list()
            all_subsets: list = list()
            for sublist in cnf_eff[act_name].clauses:  # TODO fix the is eff !!!
                subsets = chain.from_iterable(combinations(sublist, r) for r in range(1, len(sublist) + 1))
                all_subsets.append(list(subsets))
            all_S_comb = list(product(*all_subsets))
            for S in all_S_comb:
                prox_act_name: str = str(f"{act_name}{act_num}.{proxy_index}")
                # eff(AS) ←SurelyEff
                ef_delete: set[FullyHashedLearnedLiftedFluent] = surely_effA_delete[act.name]  # eff(AS) ←SurelyEff
                ef_add: set[FullyHashedLearnedLiftedFluent] = surely_effA_add[act.name]  # eff(AS) ←SurelyEff
                pre: set[FullyHashedLearnedLiftedFluent] = surely_preA[act.name]  # pre(AS) ←SurelyPre;
                # we need to do set difference therefore we will convert S from list of tuples to a set of lists
                S_as_clauses: set[list[int]] = {list(map(literals2index.get, sublist)) for sublist in S}
                for cl in cnf_eff[act.name].clauses.difference(S_as_clauses):
                    # pre.add() add all l in cl to pre
                    pass
                proxy_index += 1  # increase proxy action index
                '''

        # main algorithm!!!

        for action_name in L_bLA.keys():
            conj_pre[action_name] = set(literals2index.values())

        extract_clauses()

        surely_effA_add: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
        # dict like preA that holds delete and add biding for each action
        # name
        surely_effA_delete: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
        # dict like preA that holds delete and add biding for each action name
        surely_preA: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()  # all fluents who are surely preconds
        # start collect effects and preconditions for each action
        for action_name in L_bLA.keys():  # add unit clauses to add and delete effects
            surely_effA_add[action_name], surely_effA_delete[action_name] = get_and_delete_unit_clauses_eff(action_name)
            surely_preA[action_name] = {literals[abs(ind) - 1] for ind in conj_pre[action_name]}
            # add preconditions!
        # TODO create proxy actions!
            create_proxy_actions(action_name, proxy_act_ind)
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

