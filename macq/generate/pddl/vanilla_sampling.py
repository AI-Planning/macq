from ...trace import TraceList, Trace, Step
from ...generate.pddl.generator import Generator
from ...utils.timer import set_timer
from tarski.search.operations import progress
import random

MAX_TRACE_TIME = 10.0


class VanillaSampling(Generator):
    def __init__(
        self,
        plan_len: int,
        num_traces: int,
        dom: str = "",
        prob: str = "",
        problem_id: int = None,
    ):
        super().__init__(dom=dom, prob=prob, problem_id=problem_id)
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
        for _ in range(self.num_traces):
            traces.append(self.generate_single_trace())
        return traces

    @set_timer(num_seconds=MAX_TRACE_TIME)
    def generate_single_trace(self):
        """
        Generates a single trace using the uniform random sampling technique.
        Loops until a valid trace is found. Wrapper does not allow the function
        to run past the time specified by the time specified.

        Returns
        -------
        trace : Trace
            The valid trace generated.
        """
        trace = Trace()
        traces = TraceList()

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
                macq_action = self.tarski_act_to_macq(act)
                macq_state = self.tarski_state_to_macq(state)
                step = Step(macq_action, macq_state)
                trace.append(step)
                state = progress(state, act)
            if ls:
                traces.append(trace)
        return traces
