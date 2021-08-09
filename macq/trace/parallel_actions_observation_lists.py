from math import exp
from numpy import dot
from random import random
from typing import Callable, Type, List, Set
from . import ObservationLists, TraceList, Step, Action
from ..observation import Observation, NoisyPartialDisorderedParallelObservation

class ParallelActionsObservationLists(ObservationLists):
    def __init__(self, traces: TraceList, Token: Type[Observation], f3_f10: Callable = None, f11_f40: Callable = None, learned_theta: Callable = None, **kwargs):

        self.traces = []
        self.type = Token
        self.f3_f10 = f3_f10
        self.f11_f40 = f11_f40
        self.learned_theta = learned_theta
        self.tokenize(traces, **kwargs)
        # dictionary that holds the probabilities of all actions being disordered
        self.probabilities = self._calculate_all_probabilities(f3_f10, f11_f40, learned_theta)
        self.actions = {a for trace in self.traces for a in trace.actions}

    def _decision(probability):
        return random() < probability

    def _default_theta_vec(self, k : int):
        return [(1/k) for _ in range(k)]

    def _f1(self, act_x: Action, act_y: Action):
        num_shared = 0
        for obj in act_x.obj_params:
            for other_obj in act_y. obj_params:
                if obj == other_obj:
                    num_shared += 1
        return num_shared

    def _f2(self, act_x: Action, act_y: Action):
        return 1 if len(act_x.obj_params) == len(act_y.obj_params) else 0

    def _theta_x_features_calc(self, f_vec, theta_vec):
        return exp(dot(f_vec, theta_vec))

    def _calculate_probability(self, act_x, act_y):
        # calculate the probability of two given actions being disordered
        # define generic f1 and f2
        f_vec = [self._f1(act_x, act_y), self._f2(act_x, act_y)]
        # allow user to optionally define their own feature functions
        if self.f3_f10:
            f_vec.append(self.f3_f10(act_x=act_x, act_y=act_y))
        if self.f11_f40:
            f_vec.append(self.f11_f40(act_x=act_x, act_y=act_y))
        theta_vec = self.learned_theta() if self.learned_theta else self._default_theta_vec(len(f_vec))

        numerator = self._theta_x_features_calc(f_vec, theta_vec)
        other_actions = self.actions.copy()
        other_actions.discard(act_x)
        other_actions.discard(act_y)
        denominator = sum([c for c in self._theta_x_features_calc(f_vec, theta_vec)])
        return numerator/denominator

    def _calculate_all_probabilities(self, f3_f10: Callable, f11_f40: Callable, learned_theta: Callable):
        probabilities = {}
        # calculate all probabilities of ALL actions ax and ay being disordered
        for act_x in self.actions:
            for act_y in self.actions:
                # prevent comparing the same actions against themselves, prevent duplicates
                if act_x != act_y and (act_y, act_x) not in probabilities:
                    # calculate probability of act_x and act_y being disordered
                    probabilities[(act_x, act_y)] = self._calculate_probability(act_x, act_y)
        return probabilities

    def tokenize(self, traces: TraceList, **kwargs):
        Token = NoisyPartialDisorderedParallelObservation
        # build parallel action sets
        for trace in traces: 
            par_act_sets = []
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
                    
                    # if the action has any conditions in common with any actions in the previous parallel set
                    if a_conditions.intersection(cur_par_act_conditions) != set(): 
                        # add psi_k and s'_k to the final (ordered) lists of parallel action sets and states
                        par_act_sets.append(cur_par_act) 
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

            # generate disordered actions - do trace by trace
            for i in range(len(par_act_sets)):
                for j in range(len(par_act_sets)):
                    # prevent comparing the same sets
                    if i != j:
                        for act_x in par_act_sets[i]:
                            for act_y in par_act_sets[j]:
                                # get probability and divide by distance
                                prob = self.probabilities[(act_x, act_y)]/(j - i)
                                if self._decision(prob):
                                    par_act_sets[i].discard(act_x)
                                    par_act_sets[i].add(act_y)
                                    par_act_sets[j].discard(act_y)
                                    par_act_sets[j].add(act_x)

            tokens = []
            for i in range(len(par_act_sets)):
                for act in par_act_sets[i]:
                    tokens.append(Token(Step(state=states[i], action=act, index=i), par_act_set_ID = i, **kwargs))
            self.append(tokens)            
        