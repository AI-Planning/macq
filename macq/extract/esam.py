from ..observation import ObservedTraceList
from ..trace import Action, Fluent, State, PlanningObject
from ..extract import Model
from ..extract.learned_action import ParameterBoundLearnedLiftedAction
from ..extract.learned_fluent import LearnedLiftedFluent, PHashLearnedLiftedFluent
from itertools import product
from nnf import And, Or, Var
from ..extract.sam import sort_inference, DisjointSet
from ..extract.Sort import Sort
import sys


def make_PHashFluent_set(action: Action, flu: Fluent, action_2_sort: dict[str, list[str]], fluent_types=None)\
        -> set[PHashLearnedLiftedFluent]:
    """
    Args:
        action_2_sort: map of action_name mapped to the action's sort list
        action: the action
        flu: the fluent
        fluent_types: dict that maps each fluent to a list of the types he accepts by order.


    Returns: all FullyHashedLiftedFluent instances of 'flu' in action. FullyHashedLiftedFluent may have same
    name and sorts but differ in param_act_inds.
    for example:
    assume o1 is of type object.
    action = act(o1,o1)
    flu= lit(O1)
    output = {('lit', [object], [1]), ('lit', [object], [2])}

    Parameters
    ----------
    """
    ret: set[PHashLearnedLiftedFluent] = set()
    all_act_inds: list[list[int]] = list(map(list,
                                             product(*find_indexes_in_l2(flu.objects, action.obj_params))))
    sorts: list[str] = [action_2_sort[action.name][i] for i in all_act_inds[0]] if fluent_types is None else fluent_types[flu.name]
    if all(len(act_inds) > 0 for act_inds in all_act_inds):
        for act_inds in all_act_inds:  # for each product add the matching fluent information to the dict
            ret.add(PHashLearnedLiftedFluent(flu.name, sorts, list(act_inds)))
    return ret


class ESAM:

    objects_names_2_types: [str, str] = dict()

    def __new__(cls,
                obs_trace_list: ObservedTraceList = None,
                debug=False,
                recursion_limit=2000,
                obj_to_sort: dict[str, Sort] = None,
                sorts: list[Sort] = None,
                action_2_sort: dict[str, list[str]] = None,
                fluent_types: [str, list]=None,
                **kwargs
                ) -> Model:
        """ learns from fully observable observations under no further assumptions to extract a safe lifted action model
        of the problem's domain.
            Args:
                obs_trace_list(ObservedTraceList): tokenized TraceList.
                recursion_limit(int): maximum recursion limit, option to change recursion limit, essential when trying
                 to solve complex cnf equations
                action_2_sort(dict str -> list[str]): optional, a map that maps the sorts of each action parameters
                obj_to_sort(dict: str-> Sort): optional, a map that maps the sorts of each object parameters
                sorts(list[Sort]): optional, sorts in the domain ordered s.t the parent is always before the child
                for example- {"load-truck": ["obj", "obj", "loc"], "unload-truck": ["obj", "obj", "loc"],....}
                debug(bool): defaults to False. if True, prints debug.
                                :return:
                                   a model based on ESAM learning
                                """
        sys.setrecursionlimit(recursion_limit)
        if debug:
            actions = obs_trace_list.get_actions()
            for a in actions:
                print(a)
        def extract_clauses() -> (tuple[dict[str, set[int]], dict[str, And[Or[Var]]]]):
            """
            Returns: conjunction of the number that represents fluents that must appear as preconditions (con_pre).
            conjunction of number(positive for add effect, negative for delete effect) that represents fluents that
            may appear as an effect.
            """

            if debug:
                print("initializing conjunction of preconditions for each action")
            con_pre: dict[str, set[int]] = dict()  # represents parameter bound literals mapped by action, of pre-cond
            cnf_ef: dict[str, And[Or[Var]]] = dict()  # represents parameter bound literals mapped by action, of eff
            cnf_ef_as_set: dict[str, set[Or[Var]]] = dict()
            vars_to_forget: dict[str, set[int]] = dict()  # will be used when minimizing effects cnf
            for n in {a.name for a in actions_in_traces}:  # init set for each name
                con_pre[n] = {literals2index[lit] for lit in L_bLA[n]}
                vars_to_forget[n] = set()
                cnf_ef[n] = And()
                cnf_ef_as_set[n] = set()

            def remove_redundant_preconditions():
                """removes all parameter-bound literals that there groundings are not pre-state"""
                for tr in transitions:
                    to_remove: set[int] = set()
                    pre_state: State = tr[0].state
                    for i in con_pre[a.name]:
                        lif_flu = literals[i-1]
                        if all(ind <= len(a.obj_params) for ind in lif_flu.param_act_inds):
                            fluent = Fluent(lif_flu.name,
                                            [a.obj_params[ob_index] for ob_index in lif_flu.param_act_inds])
                            if ((fluent not in pre_state.fluents.keys())
                                    or not pre_state.fluents[fluent]):
                                # unbound or if not true, means, preA contains at the end only true value fluents
                                to_remove.add(literals2index[lif_flu])
                    con_pre[a.name].difference_update(to_remove)

            def make_cnf_eff():
                """add all parameter-bound literals that may be an effect to cnf formula as is_eff(lit_num)"""
                for tr in transitions:
                    pre_state: State = tr[0].state
                    post_state: State = tr[1].state
                    for grounded_flu, val in pre_state.fluents.items():
                        if all(ob in a.obj_params for ob in grounded_flu.objects):
                            if grounded_flu not in post_state.keys() or post_state[grounded_flu] != val:
                                c_eff: list[Var] = list()
                                'we use the call below to get all know param act inds for fluents'
                                fluents: set[PHashLearnedLiftedFluent] =\
                                    make_PHashFluent_set(a, grounded_flu, action_2_sort=action_2_sort, fluent_types=fluent_types)
                                for flu in fluents:
                                    if val:
                                        c_eff.append(Var(-literals2index[flu]))
                                    else:
                                        c_eff.append(Var(literals2index[flu]))
                                cnf_ef_as_set[a.name].add(Or(c_eff))



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
                                not_eff = Var(literals2index[flu], False)
                                # cnf_ef_as_set[a.name].add(Or([not_eff]))  TODO change this
                                vars_to_forget[a.name].add(literals2index[flu])
                            else:
                                not_eff = Var(-literals2index[flu], False)
                                # cnf_ef_as_set[a.name].add(Or([not_eff])) TODO change this
                                vars_to_forget[a.name].add(-literals2index[flu])


            if debug:
                print("removing redundant preconditions based on transitions")
                print(" adding effects based on transitions")
            for a, transitions in obs_trace_list.get_all_transitions().items():  # sas is state-action-state
                if isinstance(a, Action):
                    remove_redundant_preconditions()
                    make_cnf_eff()
            if debug:
                print("adding not(is_eff(l)) clauses to cnf of is_eff")
            for a, transitions in obs_trace_list.get_all_transitions().items():
                for trans in transitions:
                    add_not_iseff(trans[1].state)  # trans[1].state is the post state
            # last step of function is to minimize all cnf of effects.
            if debug:
                print("minimizing effects cnf of each action")

            for k, v in cnf_ef_as_set.items():
                cnf_ef[k] = And(v)

            for a_name in L_bLA.keys():
                print(f"{a_name} cnf is: {cnf_ef[a_name]}\n")
                print(f"{a_name} vars_to forget are: {vars_to_forget[a_name]}\n")
                cnf_ef[a_name] = cnf_ef[a_name].forget(vars_to_forget[a_name])
                print(f"{a_name} cnf after forget is: {cnf_ef[a_name]}")
                cnf_ef[a_name] = cnf_ef[a_name].implicates()
                print(f"{a_name} cnf after minimization is: {cnf_ef[a_name]}\n==================")

            return con_pre, cnf_ef

        # start of algorithm
        # step 0- initiate all class data structures.

        if obj_to_sort is None or action_2_sort is None: # todo fix the condition  # added code ========================
            action_2_sort: dict[str, list[str]] = dict()
            sort_dict: dict[str, str]
            if obs_trace_list is not None:
                obs_trace_list = obs_trace_list
                # sort_dict = sort_inference(obs_trace_list)
                sort_dict =sort_inference(obs_trace_list)
                cls.objects_names_2_types = sort_dict
                for act in obs_trace_list.get_actions():
                    if act.name not in action_2_sort.keys():
                        action_2_sort[act.name] = [sort_dict[ob.name] for ob in act.obj_params]

        else:
            cls.objects_names_2_types = {k: v.sort_name for k,v in obj_to_sort.items()}

        if debug:
            print(action_2_sort.__str__())

        literals2index: dict[PHashLearnedLiftedFluent, int] = dict()
        literals: list[PHashLearnedLiftedFluent] = list()
        actions_in_traces: set[Action] = obs_trace_list.get_actions() if obs_trace_list is not None else None
        # the sets below are the arguments the model constructor requires and are the endpoint of this algorithm
        learned_actions: set[ParameterBoundLearnedLiftedAction] = set()
        learned_fluents: set[LearnedLiftedFluent] = set()

        # step 1, collect all literals binding of each action
        L_bLA: dict[str, set[PHashLearnedLiftedFluent]] = {act.name: set() for act in actions_in_traces}
        if debug:
            print("initiating process of collecting all L_bla possible for actions")
        for f in obs_trace_list.get_fluents():  # for every fluent in the acts fluents
            for act in actions_in_traces:
                if all(ob in act.obj_params for ob in f.objects):
                    L_bLA[act.name].update(make_PHashFluent_set(action=act,
                                                                flu=f,
                                                                action_2_sort=action_2_sort,
                                                                fluent_types=fluent_types))

        # step 2, construct useful data structures to access meaningful information
        literals: list[PHashLearnedLiftedFluent] = list(set().union(*L_bLA.values()))
        all_flus: set[Fluent] = obs_trace_list.get_fluents()


        for index, l in enumerate(literals):
            literals2index[l] = index+1

        # step 3, extract cnf of effects and conjunction of preconditions using extract_clauses method
        if debug:
            print("starting 'extract clauses algorithm'")
        conj_pre, cnf_eff = extract_clauses()

        # step 4, make all lifted actions based on lifted pre\add\delete fluents of action
        surely_preA: dict[str, set[PHashLearnedLiftedFluent]] = dict()  # all fluents who are surely preconds
        proxy_act_ind: int = 1  # counts action number, each action has different number, each proxy has extra info
        if debug:
            print("starting creation of proxy actions")

        for action_name in L_bLA.keys():
            if debug:
                print(f"creating proxy actions for action: {action_name}")
                print(f"\ncnf-eff for act {action_name} = {cnf_eff[action_name]}")

            surely_preA[action_name] = {literals[abs(ind) - 1] for ind in conj_pre[action_name]}
            # create proxy actions
            proxy_index = 0
            for model in cnf_eff[action_name].models():
                proxy_index += 1  # increase counter of proxy action
                if debug:
                    print(f"model{proxy_index} is:  {model.__str__()}")

                m: dict[PHashLearnedLiftedFluent, bool] = {literals[abs(ind) - 1]: model[ind] for ind
                                                           in model.keys() if isinstance(ind, int) and ind > 0}
                m.update({literals[abs(ind) - 1]: not model[ind] for ind
                                                           in model.keys() if isinstance(ind, int) and ind < 0})
                is_to_skip: bool = False  # skip the loop because no negative preconditions are allowed in strips?
                for ind in model.keys():
                    if isinstance(ind, int) and not model[ind] and ind < 0:  # check if there are proxy's neg precond
                        is_to_skip = True
                        break
                if is_to_skip:
                    continue

                proxy_act_name = str(f"{action_name}_{proxy_act_ind}_{proxy_index}")
                add_eff: set[PHashLearnedLiftedFluent] = {literals[ind - 1] for ind in model.keys() if
                                                          isinstance(ind, int) and model[ind] and ind > 0}
                del_eff: set[PHashLearnedLiftedFluent] = {literals[abs(ind) - 1] for ind in model.keys() if
                                                          isinstance(ind, int) and model[ind] and ind < 0}
                pre: set[PHashLearnedLiftedFluent] = surely_preA[action_name].union(
                    {literals[abs(ind) - 1] for ind in model.keys() if
                     isinstance(ind, int) and not model[ind] and ind > 0})

                new_ind_dict = cls.minimize_parameters(model_dict=m,
                                                       act_num_of_param=len(action_2_sort[action_name]))
                reversed_dict: dict[int, int] = {v: k for k, v in new_ind_dict.items()}
                param_sorts: list[str] = list()
                for i in range(len(reversed_dict.keys())):
                    param_sorts.append(action_2_sort[action_name][reversed_dict[i]])


                learned_actions.add(
                    ParameterBoundLearnedLiftedAction(proxy_act_name,
                                        param_sorts=param_sorts,
                                        precond=cls.modify_fluent_params(pre, new_ind_dict),
                                        add=cls.modify_fluent_params(add_eff, new_ind_dict),
                                        delete=cls.modify_fluent_params(del_eff, new_ind_dict)))

            if debug:
                print(f"created {proxy_index} proxy actions for action: {action_name}")
                print("======================================================================")
            proxy_act_ind += 1  # increase counter of base action by 1

        # construct the model using the actions and fluents set we concluded from traces
        learned_fluents.update(set(map(PHashLearnedLiftedFluent.to_LearnedLiftedFluent, literals)))
        return Model(learned_fluents, learned_actions, sorts if sorts else None)

    @staticmethod
    def minimize_parameters(model_dict:  dict[PHashLearnedLiftedFluent, bool],
                            act_num_of_param: int) -> dict[int, int]:
        """
        the method computes the minimization of parameter list
        Args:
            pre: set of positive preconditions
            act_num_of_param: the length of action's param's list
            model_dict: represents the cnf, maps each literal to its grounded value
        Returns:
            a dictionary mapping each original param act ind_ to the new actions minimized parameter list
        """
        # make a table that determines if an act ind 'i' is an effect in all occurrences of F, nad is bound to index 'j'
        #  in F, minimize i with all indexes t who are bound to 'j' in F in all true occurrences of F

        ret_dict: dict[int, int] = dict()
        if len(model_dict.keys()) == 0:
            return ret_dict

        ind_occ: dict[str, list[set[int]]] = dict()
        for f in model_dict.keys():
            ind_occ[f.name] = (list())
            for _ in range(len(f.param_act_inds)):
                ind_occ[f.name].append(set())

        not_to_minimize: set[int] = set()

        for f, val in model_dict.items():
            if not val:
                not_to_minimize.update(f.param_act_inds)

        ind_sets = DisjointSet(act_num_of_param)
        for f, val in model_dict.items():
            for i in range(len(f.param_act_inds)):
                if f.param_act_inds[i] not in not_to_minimize:
                    ind_occ[f.name][i].add(f.param_act_inds[i])

        for i in set(range(act_num_of_param)).difference(not_to_minimize):
            for f, set_list in ind_occ.items():
                for sett in set_list:
                    if i in sett:
                        for j in sett:
                            ind_sets.union_by_rank(i, j)

        ugly_inds: list[int] = list({ind_sets.find(i) for i in range(act_num_of_param)})
        ugly_inds.sort()
        for i in range(act_num_of_param):
            ret_dict[i] = ugly_inds.index(ind_sets.find(i))

        return ret_dict

    @staticmethod
    def modify_fluent_params(fluents: set[PHashLearnedLiftedFluent],
                             param_dict: dict[int, int]) -> set[PHashLearnedLiftedFluent]:

        new_set: set[PHashLearnedLiftedFluent] = set()
        for f in fluents:
            new_f = PHashLearnedLiftedFluent(name=f.name, param_sorts=f.param_sorts,
                                             param_act_inds=[param_dict[i] for i in f.param_act_inds])
            new_set.add(new_f)
        return new_set


def find_indexes_in_l2(
        l1: list[PlanningObject],
        l2: list[PlanningObject])\
        -> (list[list[int]]):
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