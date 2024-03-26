from ..trace import Action, Fluent, State
from ..extract import model, LearnedLiftedAction
from ..extract.learned_fluent import LearnedLiftedFluent, FullyHashedLearnedLiftedFluent
from ..observation import Observation, ObservedTraceList


class FluentInfo:
    name: str
    sorts: list[str]
    param_act_inds: list[int]

    def __init__(self, name: str, sorts: list[str], param_act_inds: list[int]):
        self.name = name
        self.sorts = sorts
        self.param_act_inds = param_act_inds

    def __eq__(self, other):
        return isinstance(other, FluentInfo) and hash(self) == hash(other)

    def __hash__(self):
        return hash(f"{self.name} {self.sorts} {self.param_act_inds}")


class SAMgenerator:
    """DESCRIPTION
    an object that handles all traces data and manipulates it in order to generate a model based on SAM algorithm
    """
    obs_trace_list: ObservedTraceList
    L_bLA: dict[str, set[FluentInfo]] = dict()  # represents all parameter bound literals mapped by action
    effA_add: dict[str, set[FluentInfo]] = dict()  # dict like preA that holds delete and add biding for each action
    # name
    effA_delete: dict[str, set[FluentInfo]] = dict()  # dict like preA that holds delete and add biding for each action
    # name
    #  add is 0 index in tuple and delete is 1
    preA: dict[str, set[FluentInfo]] = dict()  # represents  parameter bound literals mapped by action, of pre-cond
    # LiftedPreA, LiftedEFF both of them are stets of learned lifted fluents
    learned_lifted_fluents: set[LearnedLiftedFluent] = set()
    learned_lifted_action: set[LearnedLiftedAction] = set()
    action_2_sort: dict[str, list[str]] = dict()

    # =======================================Initialization of data structures======================================
    def __init__(self, obs_trace_list: ObservedTraceList = None,
                 action_2_sort: dict[str, list[str]] = None, debug=False):
        """Creates a new SAMgenerator instance.
               Args:
                    obs_trace_list(ObservedTraceList):
                        observed traces from the same domain.
                    action_2_sort(dict str -> list[str])
                """
        if obs_trace_list is not None:
            self.obs_trace_list = obs_trace_list
            self.action_2_sort = action_2_sort
            self.update_L_bLA()

    # =======================================UPDATE FUNCTIONS========================================================
    def update_L_bLA(self):
        """collects all parameter bound literals and maps them based on action name
                values of dict is a set[(fluent.name: str, sorts:list[str], param_inds:set[int])]"""
        actions_in_traces: set[Action] = self.obs_trace_list.get_actions()
        for f in self.obs_trace_list.get_fluents():  # for every fluent in the acts fluents
            for act in actions_in_traces:
                if act.name not in self.L_bLA.keys():
                    self.L_bLA[act.name] = set()
                param_indexes_in_literal: list[int] = list()  # initiate a set of ints
                sorts: list[str] = list()

                if all(ob in act.obj_params for ob in f.objects):  # check to see if all fluent objects are
                    # bound to action parameters
                    i: int = 0
                    for obj in act.obj_params:  # for every object in the parameters
                        if obj in f.objects:  # if the object is true in fluent then
                            param_indexes_in_literal.append(i)  # append obj index to
                            sorts.append(self.action_2_sort[act.name].__getitem__(i))  # append obj sort
                        i += 1
                    self.L_bLA[act.name].add(FluentInfo(f.name, sorts, param_indexes_in_literal))
        self.preA = self.L_bLA.copy()

    # =======================================ALGORITHM LOGIC========================================================
    def remove_redundant_preconditions(self, act: Action, transitions: list[list[Observation]]):
        # based on lines 6 to 8 in paper
        """removes all parameter-bound literals that there groundings are not pre-state"""
        for trans in transitions:
            pre_state: State = trans[0].state
            to_remove: set[FluentInfo] = set()
            for flu_inf in self.preA[act.name]:
                fluent = Fluent(flu_inf.name, [obj for obj in act.obj_params if
                                               act.obj_params.index(obj) in flu_inf.param_act_inds])
                if (fluent in pre_state.fluents.keys()) and not pre_state.fluents[fluent]:  # remove if
                    # unbound or if not true, means, preA contains at the end only true value fluents
                    to_remove.add(flu_inf)
            for flu_inf in to_remove:
                self.preA[act.name].remove(flu_inf)

    # based on lines 9 to 11 in paper
    def add_surely_effects(self, act: Action, transitions: list[list[Observation]]):
        """add all parameter-bound literals that are surely an effect"""
        for trans in transitions:
            pre_state: State = trans[0].state
            post_state: State = trans[1].state
            # add all add_effects of parameter bound literals
            self.add_literal_binding_to_eff(post_state, pre_state, act, add_delete="add")
            # add all delete_effects of parameter bound literals
            self.add_literal_binding_to_eff(pre_state, post_state, act, add_delete="delete")

    def add_literal_binding_to_eff(self, s1: State, s2: State, act: Action,
                                   add_delete="add"):
        """gets all fluents in the difference of s1-s2 and add all binding that
           appears in difference to self.eff_'add_delete'[act.name]
           Args:
                    s1 (State):
                        the state on the left side of the difference
                    s2(State):
                        the state on the right side of the difference.
                    act(Action):
                        the action of the effect
                    add_delete(str):
                        if ="add" it adds literal binding to add_effect
                        if ="delete" it adds literal binding to the delete_effect
           """
        for k, v in s1.fluents.items():
            if (not (k in s2.keys() and s2.fluents[k] == v)) and v:
                param_indexes_in_literal: list[int] = list()
                fluent_name = k.name
                sorts: list[str] = list()
                i: int = 0
                for obj in act.obj_params:  # for every object in parameters, if object is in fluent, add its index
                    if obj in k.objects:
                        param_indexes_in_literal.append(i)
                        sorts.append(self.action_2_sort.get(act.name).__getitem__(i))
                    i += 1
                    # for j in range(sorts.__len__()):
                    #     if not param_indexes_in_literal.__contains__(j):
                    #         sorts.pop(i-1)
                bla: FluentInfo = FluentInfo(fluent_name, sorts, param_indexes_in_literal)
                if add_delete == "delete":
                    if act.name in self.effA_delete.keys():  # if action name exists in dictionary
                        # then add
                        self.effA_delete[act.name].add(bla)  # add it to add effect
                    else:
                        self.effA_delete[act.name] = {bla}

                if add_delete == "add":
                    if act.name in self.effA_add.keys():  # if action name exists in dictionary then add
                        self.effA_add[act.name].add(bla)  # add it to add effect
                    else:
                        self.effA_add[act.name] = {bla}

    def loop_over_action_triplets(self):
        """implement lines 5-11 in the SAM paper
        calls dd_surely_effects and remove_redundant_preconditions to make pre-con(A) , Eff(A)"""
        self.obs_trace_list.get_all_transitions()
        for act, transitions in self.obs_trace_list.get_all_transitions().items():  # sas is state-action-state
            if isinstance(act, Action):
                self.remove_redundant_preconditions(act, transitions)
                self.add_surely_effects(act, transitions)

    # =======================================finalize and return a model============================================
    def make_act_lifted_fluent_set(self, act_name: str,
                                   keyword="PRE") -> (
            set)[FullyHashedLearnedLiftedFluent]:
        """ make the fluent set for an action based on the keyword provided
        Args:
                    act_name (str):
                        the state on the left side of the difference
                    keyword(str):
                        if "PRE" makes all lifted preconditions for action.
                        if "ADD" makes all lifted add effects for action
                        if "DELETE" makes all lifted delete effects for action
                    """
        learned_fluents_set = set()
        if keyword == "PRE":
            for flu_inf in self.preA[act_name]:
                lifted_fluent = FullyHashedLearnedLiftedFluent(flu_inf.name, flu_inf.sorts, flu_inf.param_act_inds)
                learned_fluents_set.add(lifted_fluent)

        if keyword == "ADD":
            for flu_inf in self.effA_add.get(act_name):
                lifted_fluent = FullyHashedLearnedLiftedFluent(flu_inf.name, flu_inf.sorts, flu_inf.param_act_inds)
                learned_fluents_set.add(lifted_fluent)
        if keyword == "DELETE":
            for flu_inf in self.effA_delete[act_name]:
                lifted_fluent = FullyHashedLearnedLiftedFluent(flu_inf.name, flu_inf.sorts, flu_inf.param_act_inds)
                learned_fluents_set.add(lifted_fluent)
        return learned_fluents_set

    def make_learned_fluent_set(self):
        """ unionize all fluents of action to make a set of all fluents in domain,
         ignores differences of param_act_inds"""
        for lift_act in self.learned_lifted_action:
            precond = set([f.to_LearnedLiftedFluent() for f in lift_act.precond if
                           (isinstance(f, FullyHashedLearnedLiftedFluent) and
                            lift_act.precond is not None)])
            add = set([f.to_LearnedLiftedFluent() for f in lift_act.add if
                       (isinstance(f, FullyHashedLearnedLiftedFluent) and
                        lift_act.add is not None)])
            delete = set([f.to_LearnedLiftedFluent() for f in lift_act.delete if
                          (isinstance(f, FullyHashedLearnedLiftedFluent) and
                           lift_act.delete is not None)])

            self.learned_lifted_fluents.update(set() if precond is None else precond,
                                               set() if add is None else add,
                                               set() if delete is None else delete)

    def make_lifted_instances(self):
        """makes the learned lifted and learned fluents set based
          on the collected data in add,delete and pre dicts"""
        # {act_name:{pre:set,add:set,delete:set}}
        # for each action that was observed do:
        for action_name in self.L_bLA.keys():
            learned_act_fluents: dict[str, set[FullyHashedLearnedLiftedFluent]] = dict()
            # make all action's pre-condition fluents and add to set
            learned_act_fluents["precond"] = self.make_act_lifted_fluent_set(action_name, keyword="PRE")
            # make all action's add_eff fluents and add to set
            learned_act_fluents["add"] = self.make_act_lifted_fluent_set(action_name, keyword="ADD")
            # make all action's delete_eff fluents and add to set
            learned_act_fluents["delete"] = self.make_act_lifted_fluent_set(action_name, keyword="DELETE")
            # make learned lifted action instance
            lifted_act = LearnedLiftedAction(action_name, self.action_2_sort[action_name],
                                             precond=learned_act_fluents["precond"],
                                             add=learned_act_fluents["add"], delete=learned_act_fluents["delete"])
            # add learned_lifted action to all learned actions set
            self.learned_lifted_action.add(lifted_act)
        # initiate a learned fluent set
        self.make_learned_fluent_set()

    def generate_model(self) -> model.Model:
        self.loop_over_action_triplets()
        self.make_lifted_instances()
        return model.Model(self.learned_lifted_fluents, self.learned_lifted_action)

    # =======================================THE CLASS ============================================


class SAM:
    __sam_generator = None

    def __new__(cls, obs_trace_list: ObservedTraceList = None,
                action_2_sort: dict[str, list[str]] = None, sam_generator: SAMgenerator = None):
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
        if sam_generator is not None:
            cls.__sam_generator = sam_generator
        else:
            cls.__sam_generator: SAMgenerator = SAMgenerator(obs_trace_list=obs_trace_list, action_2_sort=action_2_sort)

        return cls.__sam_generator.generate_model()
