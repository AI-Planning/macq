from typing import Type
from . import ObservationLists, TraceList, Step
from ..observation import Observation, NoisyPartialDisorderedParallelObservation

class ParallelActionsObservationLists(ObservationLists):
    def __init__(self, traces: TraceList, Token: Type[Observation], **kwargs):
        self.traces = []
        self.type = Token
        self.tokenize(traces, **kwargs)


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
            tokens = []
            for i in range(len(par_acts)):
                par_act_set = par_acts[i]
                for act in par_act_set:
                    tokens.append(Token(Step(state=states[i], action=act, index=i), par_act_set_ID = i))
            self.append(tokens)            
        # TODO: generate disordered actions