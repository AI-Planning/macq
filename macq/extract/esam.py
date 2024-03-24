from ..observation import ObservedTraceList
from ..trace import Action, Fluent, State, PlanningObject
from ..extract import LearnedLiftedAction, Model
from ..extract.learned_fluent import LearnedLiftedFluent, FullyHashedLearnedLiftedFluent
from itertools import product
from nnf import And, Or, Var, false
from .infer_sort_type import type_inference


class ESAM:

    def __new__(cls, obs_trace_list: ObservedTraceList = None, action_2_sort: dict[str, list[str]] = None, debug=False):
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
        literals: list[FullyHashedLearnedLiftedFluent] = list()

        # the sets below are the arguments the model constructor requires and are the endpoint of this algorithm
        learned_actions: set[LearnedLiftedAction] = set()
        learned_fluents: set[LearnedLiftedFluent] = set()

        def make_FullyHashedFluent_set(acton: Action, flu: Fluent) -> set[FullyHashedLearnedLiftedFluent]:
            ret: set[FullyHashedLearnedLiftedFluent] = set()
            all_act_inds: list[list[int]] = list(map(list, product(*find_indexes_in_l2(flu.objects, acton.obj_params))))
            sorts: list[str] = [action_2_sort[acton.name][i] for i in all_act_inds[0]]
            if all(len(act_inds) > 0 for act_inds in all_act_inds):
                for act_inds in all_act_inds:  # for each product add the matching fluent information to the dict
                    ret.add(FullyHashedLearnedLiftedFluent(flu.name, sorts, list(act_inds)))
            return ret

        actions_in_traces: set[Action] = obs_trace_list.get_actions()
        # step 1, collect all literals binding of each action
        L_bLA: dict[str, set[FullyHashedLearnedLiftedFluent]] = {act.name: set() for act in actions_in_traces}

        if debug:
            print("initiating process of collecting all L_bla possible for actions")
        for f in obs_trace_list.get_fluents():  # for every fluent in the acts fluents
            for act in actions_in_traces:
                if all(ob in act.obj_params for ob in f.objects):
                    L_bLA[act.name].update(make_FullyHashedFluent_set(act, f))

        literals: list[FullyHashedLearnedLiftedFluent] = list(set().union(*L_bLA.values()))
        for index, l in enumerate(literals):
            literals2index[l] = index+1

        conj_pre: dict[str, set[int]] = dict()  # represents parameter bound literals mapped by action, of pre-cond
        cnf_eff: dict[str, And[Or[Var]]] = dict()  # represents parameter bound literals mapped by action, of eff
        lit_2_delete_from_clauses: dict[str, set[int]] = dict()  # will help us in the unit propagation""

        if debug:
            print("initializing conjunction of preconditions for each action")
        for name in {a.name for a in actions_in_traces}:  # init set for each name
            conj_pre[name] = {literals2index[lit] for lit in L_bLA[name]}
            lit_2_delete_from_clauses[name] = set()
            cnf_eff[name] = And()

        var_to_forget: dict[str, set[int]] = dict()    # well use it later on to "forget" not_iseff fluents
        for name in {a.name for a in actions_in_traces}:
            var_to_forget[name] = set()

        def extract_clauses() -> (list[list[FullyHashedLearnedLiftedFluent]],
                                  list[list[FullyHashedLearnedLiftedFluent]]):
            def remove_redundant_preconditions():
                """removes all parameter-bound literals that there groundings are not pre-state"""
                for tr in transitions:
                    to_remove: set[int] = set()
                    pre_state: State = tr[0].state
                    for i in conj_pre[a.name]:
                        lif_flu = literals[i-1]
                        if all(ind <= len(a.obj_params) for ind in lif_flu.param_act_inds):
                            fluent = Fluent(lif_flu.name,
                                            [a.obj_params[ob_index] for ob_index in lif_flu.param_act_inds])
                            if (fluent not in pre_state.fluents.keys()) or not pre_state.fluents[fluent]:
                                'unbound or if not true, means, preA contains at the end only true value fluents'
                                to_remove.add(literals2index[lif_flu])
                    conj_pre[a.name].difference_update(to_remove)

            def make_cnf_eff():
                """add all parameter-bound literals that are surely an effect"""
                for tr in transitions:
                    pre_state: State = tr[0].state
                    post_state: State = tr[1].state
                    for grounded_flu, v in pre_state.fluents.items():
                        if all(ob in a.obj_params for ob in grounded_flu.objects):
                            if grounded_flu not in post_state.keys() or post_state[grounded_flu] != v:
                                c_eff: Or[Var] = Or(false)
                                'we use the call below to get all know param act inds for fluents'
                                fluents: set[FullyHashedLearnedLiftedFluent] = make_FullyHashedFluent_set(a,
                                                                                                          grounded_flu)
                                for flu in fluents:
                                    if v:
                                        c_eff = c_eff.__or__(Var(-literals2index[flu]))
                                    else:
                                        c_eff = c_eff.__or__(Var(literals2index[flu]))
                                cnf_eff[a.name] = cnf_eff[a.name].__and__(c_eff)
            if debug:
                print("removing redundant preconditions based on transitions")
                print(" adding effects based on transitions")
            for a, transitions in obs_trace_list.get_all_transitions().items():  # sas is state-action-state
                if isinstance(a, Action):
                    remove_redundant_preconditions()
                    make_cnf_eff()

            def add_not_iseff(post_state: State):
                """delete literal from cnf_eff_del\add of function if it hadn't occurred in some post state of the
                action """
                for flu in literals:
                    if max(flu.param_act_inds)+1 <= len(a.obj_params):
                        """print(f"act ind for flu:{flu.name} {flu.param_act_inds}")
                        print(f"length of action params is: {len(a.obj_params)}")"""
                        fluent = Fluent(f.name, [a.obj_params[ind] for ind in sorted(flu.param_act_inds)])
                        if fluent in post_state.fluents.keys():
                            if not post_state.fluents[fluent]:
                                cnf_eff[a.name] = cnf_eff[a.name].__and__(Var(literals2index[flu], False))
                                var_to_forget[a.name].add(literals2index[flu])
                            else:
                                cnf_eff[a.name] = cnf_eff[a.name].__and__(Var(-literals2index[flu], False))
                                var_to_forget[a.name].add(-literals2index[flu])

            if debug:
                print("adding not(is_eff(l)) clauses to cnf of is_eff")
            for a, transitions in obs_trace_list.get_all_transitions().items():
                for trans in transitions:
                    add_not_iseff(trans[1].state)  # trans[1].state is the post state

            if debug:
                print("minimizing effects cnf of each action")
            for a_name in L_bLA.keys():
                cnf_eff[a_name] = cnf_eff[a_name].to_CNF()
                cnf_eff[a_name] = cnf_eff[a_name].implicates()
                cnf_eff[a_name] = cnf_eff[a_name].forget(var_to_forget[a_name])

        if debug:
            print("starting 'extract clauses algorithm'")
        extract_clauses()

        surely_preA: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()  # all fluents who are surely preconds
        # start collect effects and preconditions for each action\
        proxy_act_ind: int = 1  # counts action number, each action has different number, each proxy has extra info

        if debug:
            print("starting creation of proxy actions")
        for action_name in L_bLA.keys():
            if debug:
                print(f"creating proxy actions for action: {action_name}")
            surely_preA[action_name] = {literals[abs(ind) - 1] for ind in conj_pre[action_name]}
            'create proxy actions!'
            proxy_index = 0
            mod = list(cnf_eff[action_name].models())
            for model in cnf_eff[action_name].models():
                proxy_index += 1  # increase counter of proxy action
                proxy_act_name = str(f"{action_name}_{proxy_act_ind}_{proxy_index}")
                add_eff: set[FullyHashedLearnedLiftedFluent] = {literals[ind - 1] for ind in model.keys() if
                                                                isinstance(ind, int) and model[ind] and ind > 0}
                del_eff: set[FullyHashedLearnedLiftedFluent] = {literals[abs(ind) - 1] for ind in model.keys() if
                                                                isinstance(ind, int) and model[ind] and ind < 0}
                pre: set[FullyHashedLearnedLiftedFluent] = surely_preA[action_name].union(
                    {literals[abs(ind) - 1] for ind in model.keys() if
                     isinstance(ind, int) and not model[ind] and ind > 0})
                learned_actions.add(LearnedLiftedAction(proxy_act_name, param_sorts=action_2_sort[action_name],
                                                        precond=pre, add=add_eff, delete=del_eff))

            if debug:
                print(f"created {proxy_index} proxy actions for action: {action_name}")
            proxy_act_ind += 1  # increase counter of base action by 1

        # create model!
        learned_fluents.update(set(map(FullyHashedLearnedLiftedFluent.to_LearnedLiftedFluent, literals)))
        return Model(learned_fluents, learned_actions)


def find_indexes_in_l2(l1: list[PlanningObject], l2: list[PlanningObject]) -> (list[list[int]]):
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
