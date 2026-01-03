from tarski.search.operations import progress
import random
from . import Generator
from ...utils import (
    set_timer_throw_exc,
    TraceSearchTimeOut,
    InvalidTime,
    set_num_traces,
    set_plan_length,
    progress as print_progress,
)
from ...trace import (
    Step,
    Trace,
    TraceList,
)


class VanillaSampling(Generator):
    """Vanilla State Trace Sampler - inherits the base Generator class and its attributes.

    A basic state trace generator that generates traces randomly by uniformly sampling applicable actions to find plans
    of the given length.

    Attributes:
        max_time (float):
            The maximum time allowed for a trace to be generated.
        plan_len (int):
            The length of the traces to be generated.
        num_traces (int):
            The number of traces to be generated.
        traces (TraceList):
            The list of traces generated.
    """

    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        observe_pres_effs: bool = False,
        ignore_static_fluents: bool = True,  # defaults to true to not break any pre-implemented scripts
        plan_len: int = 1,
        num_traces: int = 0,
        seed: int = None,
        max_time: float = 30,
    ):
        """
        Initializes a vanilla state trace sampler using the plan length, number of traces,
        and the domain and problem.

        Args:
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
            max_time (float):
                The maximum time allowed for a trace to be generated.
            observe_pres_effs (bool):
                Option to observe action preconditions and effects upon generation.
            plan_len (int):
                The length of each generated trace. Defaults to 1.
            num_traces (int):
                The number of traces to generate. Defaults to 1.
        """
        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
            observe_pres_effs=observe_pres_effs,
            ignore_static_fluents=ignore_static_fluents
        )
        if max_time <= 0:
            raise InvalidTime()
        if seed:
            random.seed(seed)
        self.max_time = max_time
        self.plan_len = set_plan_length(plan_len)
        self.num_traces = set_num_traces(num_traces)
        if self.num_traces > 0:
            self.traces = self.generate_traces()
        else:
            self.traces = None
        if seed:
            random.seed(seed)

    def generate_traces(self):
        """Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Returns:
            A TraceList object with the list of traces generated.
        """
        traces = TraceList()
        traces.generator = self.generate_single_trace_setup(
            num_seconds=self.max_time, plan_len=self.plan_len
        )
        for _ in print_progress(range(self.num_traces)):
            traces.append(traces.generator())
        self.traces = traces
        return traces

    def generate_single_trace_setup(self, num_seconds: float, plan_len = None):
        @set_timer_throw_exc(
            num_seconds=num_seconds, exception=TraceSearchTimeOut, max_time=num_seconds
        )
        def generate_single_trace(self=self, plan_len=plan_len):
            """Generates a single trace using the uniform random sampling technique.
            Loops until a valid trace is found. The timer wrapper does not allow the function
            to run past the time specified.

            The outside function is a wrapper that provides parameters for both the timer
            wrapper and the function.

            Returns:
                A Trace object (the valid trace generated).
            """

            if not plan_len:
                plan_len = self.plan_len
            if callable(plan_len):
                plan_len = plan_len()

            trace = Trace()

            state = self.problem.init
            valid_trace = False
            while not valid_trace:
                trace.clear()
                # add more steps while the trace has not yet reached the desired length
                for j in range(plan_len):
                    # if we have not yet reached the last step
                    if len(trace) < plan_len - 1:
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

        return generate_single_trace
