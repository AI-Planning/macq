from ...trace import TraceList, Trace, Step
from ...generate.pddl.generator import Generator
from ...utils.timer import set_timer
from ..trace_errors import InvalidNumberOfTraces, InvalidPlanLength
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
        plan_len : int
            The length of each generated trace.
        num_traces : int
            The number of traces to generate.
        dom : str
            The domain filename.
        prob : str
            The problem filename.
        problem_id : int
            The ID of the problem to access.
        

        Attributes
        -------
        traces : TraceList
            The list of traces generated.
        """

    def set_num_traces(self, num_traces: int):
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
        for _ in range(self.num_traces):
            traces.append(self.generate_single_trace())
        return traces

    # @set_timer(num_seconds=MAX_TRACE_TIME)
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

        while not valid_trace:
            trace.clear()
            # add more steps while the trace has not yet reached the desired length
            for j in range(self.plan_len):
                # find the next applicable actions
                app_act = self.instance.applicable(state)
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
                step = Step(macq_state, macq_action, j + 1)
                trace.append(step)
                state = progress(state, act)

                if j == self.plan_len - 1:
                    valid_trace = True
        return trace
