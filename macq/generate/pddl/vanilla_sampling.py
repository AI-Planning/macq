from macq.trace import TraceList, Trace, Step
from macq.generate.pddl.generate import Generate
from tarski.search.operations import progress
from pathlib import Path
import random

class VanillaSampling(Generate):
    def __init__(self, dom : str, prob : str, plan_len : int, num_traces : int):
        super().__init__(dom, prob)
        self.plan_len = plan_len
        self.num_traces = num_traces
        self.traces = self.generate_traces()

        """
        Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Arguments
        ---------
        dom : str
            The domain filename.
        prob : str
            The problem filename.
        plan_len : int
            The length of each generated trace.
        num_traces : int
            The number of traces to generate.

        Attributes
        -------
        traces : TraceList
            The list of traces generated.
        """



    def generate_traces(self):
        """
        Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Returns
        -------
        traces : TraceList
            The list of traces generated.
        """

        traces = TraceList()
        trace = Trace()

        # loop through while the desired number of traces has not yet been generated
        while len(traces) < self.num_traces:
            trace.clear()
            state = self.problem.init
            # add more steps while the trace has not yet reached the desired length
            for j in range(self.plan_len):
                # find the next applicable actions
                ls = list(self.instance.applicable(state))
                # if the trace reaches a dead lock, disregard this trace and try again
                if not ls:
                    break
                # pick a random applicable action and apply it
                act = random.choice(ls)
                # create the trace and progress the state
                macq_action = self._tarski_act_to_macq(act)
                macq_state = self._tarski_state_to_macq(state)
                step = Step(macq_action, macq_state)
                trace.append(step)
                state = progress(state, act)
            if ls:
                traces.append(trace)
        return traces