from tarski.search.operations import progress
import random

from macq.trace import (
    PlanningObject,
    Fluent,
    Action,
    Step,
    State,
    Trace,
    SAS,
    TraceList,
)
from macq.generate.pddl import Generator
from macq.utils.timer import set_timer
from macq.generate.trace_errors import InvalidNumberOfTraces, InvalidPlanLength

MAX_TRACE_TIME = 30.0

class VanillaSampling(Generator):
    """Vanilla State Trace Sampler - inherits the base Generator class and its attributes.

    A basic state trace generator that Generates traces randomly by uniformly sampling applicable actions to find plans
    of the given length.

    Attributes:
        plan_len (int):
            The length of the traces to be generated.
        num_traces (int):
            The number of traces to be generated.
        traces (TraceList):
            The list of traces generated.
    """

    def __init__(
        self,
        plan_len: int,
        num_traces: int,
        dom: str = "",
        prob: str = "",
        problem_id: int = None,
        seed: int = None,
    ):
        """
        Initializes a vanilla state trace sampler using the plan length, number of traces,
        and the domain and problem.

        Args:
            plan_len (int):
                The length of each generated trace.
            num_traces (int):
                The number of traces to generate.
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
        """
        super().__init__(dom=dom, prob=prob, problem_id=problem_id)
        self.plan_len = plan_len
        self.num_traces = num_traces
        self.traces = self.generate_traces()
        if seed:
            random.seed(seed)

    def set_num_traces(self, num_traces: int):
        """Checks the validity of the number of traces and then sets it.

        Args:
            num_traces (int):
                The number of traces to set.

        Raises:
            InvalidNumberOfTraces:
                The exception raised when the number of traces provided is invalid.
        """
        if num_traces > 0:
            self.num_traces = num_traces
        else:
            raise InvalidNumberOfTraces()

    def set_plan_length(self, plan_len: int):
        """Checks the validity of the plan length and then sets it.

        Args:
            plan_len (int):
                The plan length to set.

        Raises:
            InvalidPlanLength:
                The exception raised when the plan length provided is invalid.
        """
        if plan_len > 0:
            self.plan_len = plan_len
        else:
            raise InvalidPlanLength()

    def generate_traces(self):
        """Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Returns:
            A TraceList object with the list of traces generated.
        """
        traces = TraceList()
        traces.generator = self.generate_single_trace
        for _ in range(self.num_traces):
            traces.append(self.generate_single_trace())
        return traces

    @set_timer(num_seconds=MAX_TRACE_TIME)
    def generate_single_trace(self):
        """Generates a single trace using the uniform random sampling technique.
        Loops until a valid trace is found. Wrapper does not allow the function
        to run past the time specified by the time specified.

        Returns:
            A Trace object (the valid trace generated).
        """
        trace = Trace()

        state = self.problem.init
        valid_trace = False
        while not valid_trace:
            trace.clear()
            # add more steps while the trace has not yet reached the desired length
            for j in range(self.plan_len):
                # if we have not yet reached the last step
                if j < self.plan_len - 1:
                    # find the next applicable actions
                    app_act = list(self.instance.applicable(state))
                    # if the trace reaches a dead lock, disregard this trace and try again
                    if not app_act:
                        break
                    # pick a random applicable action and apply it
                    act = random.choice(app_act)
                    # create the trace and progress the state
                    macq_action = self.tarski_act_to_macq(act)
                    macq_state = self.tarski_state_to_macq(state)
                    step = Step(macq_state, macq_action, j + 1)
                    trace.append(step)
                    state = progress(state, act)
                else:
                    macq_state = self.tarski_state_to_macq(state)
                    step = Step(state=macq_state, action=None, index=j + 1)
                    trace.append(step)
                    valid_trace = True
        return trace
