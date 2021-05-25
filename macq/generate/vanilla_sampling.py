from macq.trace import TraceList, Trace, Step
from macq.generate.generate import Generate
from tarski.search.operations import progress
from pathlib import Path
import random

class Vanilla_Sampling(Generate):
    def __init__(self, dom : str, prob : str, plan_len : int, num_traces : int):
        super().__init__(dom, prob)
        self.plan_len = plan_len
        self.num_traces = num_traces
        self.traces = self.generate_traces()
        

    def generate_traces(self):
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

        Returns
        -------
        traces : TraceList
            The list of traces generated.
        """

        traces = TraceList()
        trace = Trace()
        num_generated = 0
        # loop through while the desired number of traces has not yet been generated
        while num_generated < self.num_traces:
            num_generated += 1
            trace.clear()
            state = self.problem.init
            # True if trace is fully generated to the desired length
            valid_trace = True
            # add more steps while the trace has not yet reached the desired length
            for j in range(self.plan_len):
                # find the next applicable actions
                app_act = self.instance.applicable(state)
                # get items from generator
                ls = []
                for item in app_act:
                    ls.append(item)
                # if the trace reaches a dead end, disregard this trace and try again
                if ls == []:
                    num_generated -= 1
                    valid_trace = False
                    break
                # pick a random applicable action and apply it
                act = random.choice(ls)
                # create the trace and progress the state
                macq_action = self._tarski_act_to_macq(act)
                macq_state = self._tarski_state_to_macq(state)
                step = Step(macq_action, macq_state)
                trace.append(step)
                state = progress(state, act)
            if valid_trace:
                traces.append(trace)
        return traces

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests 
    base = Path(__file__).parent.parent.parent
    dom = (base / 'tests/pddl_testing_files/domain2.pddl').resolve()
    prob = (base / 'tests/pddl_testing_files/problem2.pddl').resolve()
    vanilla = Vanilla_Sampling(dom, prob, 10, 10)
    print(vanilla.generate_traces())