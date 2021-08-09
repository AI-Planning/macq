import math
from numpy import dot
from typing import Callable, Type
from . import ObservationLists, TraceList, Step, Action
from ..observation import Observation, NoisyPartialDisorderedParallelObservation

class ParallelActionsObservationLists(ObservationLists):
    def __init__(self, traces: TraceList, Token: Type[Observation], **kwargs):
        #TODO: take functions as parameters
        self.traces = []
        self.type = Token
        self.tokenize(traces, **kwargs)
        self.probabilities = self.__calculate_all_probabilities()
        self.actions = {a for trace in self.traces for a in trace.actions}

    def __default_theta_vec(self, k : int):
        return [(1/k) for _ in range(k)]

    def __f1(self, act_x: Action, act_y: Action):
        num_shared = 0
        for obj in act_x.obj_params:
            for other_obj in act_y. obj_params:
                if obj == other_obj:
                    num_shared += 1
        return num_shared

    def __f2(self, act_x: Action, act_y: Action):
        return 1 if len(act_x.obj_params) == len(act_y.obj_params) else 0

    def __theta_x_features_calc(self, f_vec, theta_vec):
        return math.exp(dot(f_vec, theta_vec))

    def __calculate_probability(self, act_x, act_y, f3_f10: Callable = None, f11_f40: Callable = None, learned_theta: Callable = None):
        # calculate the probability of two given actions being disordered
        # define generic f1 and f2
        f_vec = [self.__f1(act_x, act_y), self.__f2(act_x, act_y)]
        # allow user to optionally define their own feature functions
        if f3_f10:
            f_vec.append(f3_f10(act_x=act_x, act_y=act_y))
        if f11_f40:
            f_vec.append(f11_f40(act_x=act_x, act_y=act_y))
        theta_vec = learned_theta() if learned_theta else self.__default_theta_vec(len(f_vec))

        numerator = self.__theta_x_features_calc(f_vec, theta_vec)
        other_actions = self.actions.copy()
        other_actions.discard(act_x)
        other_actions.discard(act_y)
        denominator = sum([c for c in self.__theta_x_features_calc(f_vec, theta_vec)])
        return numerator/denominator

    def __calculate_all_probabilities(self):
        # TODO:
        # calculate all probabilities of ALL actions ax and ay being disordered, where ax and ay are actions in adjacent parallel action sets
        pass



    def tokenize(self, traces: TraceList, **kwargs):
        Token = NoisyPartialDisorderedParallelObservation
        # build parallel action sets
        for trace in traces: 
            par_acts = []
            states = []
            cur_par_act = set()
            cur_states = set()
            cur_par_act_conditions = set()
            a_conditions = set()
            
            # add initial state
            states.append({f for f in trace[0].state})
            # last step doesn't have an action/just contains the state after the last action
            for i in range(len(trace) - 1):
                a = trace[i].action
                if a:
                    a_conditions.update([p for p in a.precond] + [e for e in a.add] + [e for e in a.delete])
                    # assume the first action 
                    #if i == 0:
                    #    cur_par_act_conditions.update(a_conditions)

                    print(a_conditions.intersection(cur_par_act_conditions))
                    
                    # if the action has any conditions in common with any actions in the previous parallel set
                    if a_conditions.intersection(cur_par_act_conditions) != set(): 
                        # add psi_k and s'_k to the final (ordered) lists of parallel action sets and states
                        par_acts.append(cur_par_act) 
                        states.append(cur_states)
                        # reset psi_k and s'_k (that is, create a new parallel action set and corresponding state set)
                        cur_par_act = set()
                        cur_states = set()
                        # reset the conditions
                        cur_par_act_conditions = set()
                    # add the action and state to the appropriate psi_k and s'_k (either the existing ones, or
                    # new/empty ones if the current action is NOT parallel with actions in the previous set of actions.)
                    cur_par_act.add(a)
                    # take the union of fluents. note that the state AFTER the action was taken is the NEXT state.
                    cur_states.update([f for f in trace[i + 1].state])
                    cur_par_act_conditions.update(a_conditions)

            # TODO: generate disordered actions - do trace by trace
            for i in range(len(par_acts)):
                for j in range(len(par_acts)):
                    # prevent comparing the same sets against themselves
                    if i != j:
                        for act_i in par_acts[i]:
                            for act_j in par_acts[j]:
                                # divide by distance
                                probability = probability/(j - i)


            tokens = []
            for i in range(len(par_acts)):
                par_act_set = par_acts[i]
                for act in par_act_set:
                    tokens.append(Token(Step(state=states[i], action=act, index=i), par_act_set_ID = i))
            self.append(tokens)            
        