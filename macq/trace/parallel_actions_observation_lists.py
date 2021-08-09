from math import exp
from numpy import dot
from random import random
from typing import Callable, Type, List, Set
from . import ObservationLists, TraceList, Step, Action, State
from ..observation import Observation, NoisyPartialDisorderedParallelObservation

class ParallelActionsObservationLists(ObservationLists):
    def __init__(self, traces: TraceList, Token: Type[Observation] = NoisyPartialDisorderedParallelObservation, f3_f10: Callable = None, f11_f40: Callable = None, learned_theta: Callable = None, **kwargs):

        self.traces = []
        self.type = Token
        self.f3_f10 = f3_f10
        self.f11_f40 = f11_f40
        self.learned_theta = learned_theta
        self.actions = {step.action for trace in traces for step in trace if step.action}
        # dictionary that holds the probabilities of all actions being disordered
        self.probabilities = self._calculate_all_probabilities(f3_f10, f11_f40, learned_theta)
        self.tokenize(traces, Token, **kwargs)
        

    def _decision(self, probability):
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

    def _get_f_vec(self, act_x: Action, act_y: Action):
        # define generic f1 and f2
        f_vec = [self._f1(act_x, act_y), self._f2(act_x, act_y)]
        # allow user to optionally define their own feature functions
        if self.f3_f10:
            f_vec.append(self.f3_f10(act_x, act_y))
        if self.f11_f40:
            f_vec.append(self.f11_f40(act_x, act_y))      
        return f_vec  

    def _theta_dot_features_calc(self, f_vec, theta_vec):
        return exp(dot(f_vec, theta_vec))

    def _calculate_probability(self, act_x, act_y):
        # calculate the probability of two given actions being disordered
        f_vec = self._get_f_vec(act_x, act_y)
        theta_vec = self.learned_theta() if self.learned_theta else self._default_theta_vec(len(f_vec))
        numerator = self._theta_dot_features_calc(f_vec, theta_vec)
        denominator = 0
        for act_x_prime in self.actions:
            for act_y_prime in self.actions:
                if act_x_prime != act_y_prime:
                    denominator += self._theta_dot_features_calc(self._get_f_vec(act_x_prime, act_y_prime), theta_vec)
        return numerator/denominator

    def _calculate_all_probabilities(self, f3_f10: Callable, f11_f40: Callable, learned_theta: Callable):
        probabilities = {}
        # calculate all probabilities of ALL actions ax and ay being disordered
        for act_x in self.actions:
            probabilities[act_x] = {}
            for act_y in self.actions:
                # prevent comparing the same actions against themselves
                if act_x != act_y:
                    # calculate probability of act_x and act_y being disordered
                    probabilities[act_x][act_y] = self._calculate_probability(act_x, act_y)
        return probabilities

    def tokenize(self, traces: TraceList, Token: Type[Observation], **kwargs):
        # build parallel action sets
        for trace in traces: 
            par_act_sets = []
            states = []
            cur_par_act = set()
            cur_state = {}
            cur_par_act_conditions = set()
            a_conditions = set()
            fluents = {f for trace in traces for step in trace for f in step.state.fluents}
            
            # add initial state
            states.append(trace[0].state)
            # last step doesn't have an action/just contains the state after the last action
            for i in range(len(trace) - 1):
                a = trace[i].action
                if a:
                    a_conditions.update([p for p in a.precond] + [e for e in a.add] + [e for e in a.delete])
                    
                    # if the action has any conditions in common with any actions in the previous parallel set
                    if a_conditions.intersection(cur_par_act_conditions) != set(): 
                        # add psi_k and s'_k to the final (ordered) lists of parallel action sets and states
                        par_act_sets.append(cur_par_act) 
                        states.append(State(cur_state))
                        # reset psi_k and s'_k (that is, create a new parallel action set and corresponding state set)
                        cur_par_act = set()
                        cur_state = {}
                        # reset the conditions
                        cur_par_act_conditions = set()
                    # add the action and state to the appropriate psi_k and s'_k (either the existing ones, or
                    # new/empty ones if the current action is NOT parallel with actions in the previous set of actions.)
                    cur_par_act.add(a)
                    # take the union of fluents. note that the state AFTER the action was taken is the NEXT state.
                    if cur_state:
                        for f in fluents:
                            if trace[i + 1].state[f] and cur_state[f]:
                                cur_state[f] = True
                            elif not trace[i + 1].state[f] and not cur_state[f]:
                                cur_state[f] = False
                    cur_par_act_conditions.update(a_conditions)

            # generate disordered actions - do trace by trace
            for i in range(len(par_act_sets)):
                for j in range(len(par_act_sets)):
                    # prevent comparing the same sets
                    if i != j:
                        for act_x in par_act_sets[i]:
                            for act_y in par_act_sets[j]:
                                # get probability and divide by distance
                                prob = self.probabilities[act_x][act_y]/(j - i)
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
        