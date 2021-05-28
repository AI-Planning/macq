from ...trace import TraceList, Trace, Step
from ...generate.pddl.generator import Generator
from ...utils.timer import set_timer, MAX_TIME
from ..trace_errors import InvalidPlanLength, InvalidNumberOfTraces
from tarski.search.operations import progress
import random

class VanillaSampling(Generator):
    def __init__(self, dom : str, prob : str, plan_len : int, num_traces : int):
        super().__init__(dom, prob)
        self.set_plan_length(plan_len)
        self.set_num_traces(num_traces)
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

    def set_num_traces(self, num_traces : int):
        """AI is creating summary for set_num_traces

        Args:
            num_traces (int): [description]

        Raises:
            InvalidNumberOfTraces: [description]
        """
        if num_traces > 0:
            self.num_traces = num_traces
        else:
            raise InvalidNumberOfTraces()

    def set_plan_length(self, plan_len: int):
        if plan_len > 0:
            self.plan_len = plan_len
        else:
            raise InvalidPlanLength()
    
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
        for i in range(self.num_traces):
            trace = self.generate_single_trace()
            traces.append(trace)
        return traces

    @set_timer(num_seconds=MAX_TIME)
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
        
        state = self.problem.init
        valid_trace = False
        num_generated = 0
        while not valid_trace:
            num_generated += 1
            trace.clear()
            # add more steps while the trace has not yet reached the desired length
            for j in range(self.plan_len):
                # find the next applicable actions
                app_act = self.instance.applicable(state)
                # get items from generator
                ls = []
                for item in app_act:
                    ls.append(item)
                # if the trace reaches a dead lock, disregard this trace and try again
                if ls == []:
                    num_generated -= 1
                    break
                # pick a random applicable action and apply it
                act = random.choice(ls)
                # create the trace and progress the state
                macq_action = self.tarski_act_to_macq(act)
                macq_state = self.tarski_state_to_macq(state)
                step = Step(macq_action, macq_state, num_generated)
                trace.append(step)
                state = progress(state, act)

                if j == self.plan_len - 1:
                    valid_trace = True
        return trace