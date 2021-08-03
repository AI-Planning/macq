from . import ObservationLists

class ParallelActionsObservationLists(ObservationLists):
    def __init__(self, traces: TraceAPI.TraceList, Token: Type[Observation], **kwargs):
        super().__init__(traces, Token, **kwargs)

    def tokenize(self, traces: TraceAPI.TraceList):
        # TODO: implement for multiple traces after testing on one trace
        #for trace in traces: 
            par_acts = []
            states = []
            cur_par_act = set()
            cur_states = set()
            cur_par_act_conditions = set()
            for step in trace:
                a = step.action
                if a:
                    a_conditions = {[p for p in a.precond] + [e for e in a.add] + [e for e in a.delete]}
                    # if the action has any conditions in common with any actions in the previous parallel set
                    if a is not parallel with cur_par_act: 
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
                    cur_states.add(step.state)
                    cur_par_act_conditions.update(a_conditions)