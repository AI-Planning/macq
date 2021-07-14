from tarski.search.operations import progress
import random
from . import Generator
from ...utils.timer import set_timer, TraceSearchTimeOut
from ...utils.trace_utils import set_num_traces, set_plan_length
from ...observation.partial_observation import PercentError
from ...trace import (
    Step,
    State,
    Trace,
    TraceList,
)


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
        dom: str = None,
        prob: str = None,
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
        self.plan_len = set_plan_length(plan_len)
        self.num_traces = set_num_traces(num_traces)
        self.traces = self.generate_traces()
        if seed:
            random.seed(seed)

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

    @set_timer(num_seconds=MAX_TRACE_TIME, exception=TraceSearchTimeOut)
    def generate_single_trace(self, plan_len: int = None):
        """Generates a single trace using the uniform random sampling technique.
        Loops until a valid trace is found. Wrapper does not allow the function
        to run past the time specified by the time specified.

        Returns:
            A Trace object (the valid trace generated).
        """

        if not plan_len:
            plan_len = self.plan_len

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

    def goal_sampling(
        self, num_states: int, steps_deep: int, subset_size_perc: int = 1
    ):
        if subset_size_perc < 0 or subset_size_perc > 1:
            raise PercentError()
        goal_states = set()
        while len(goal_states) < num_states:
            # generate a trace of the specified length and retrieve the state of the last step
            state = self.generate_single_trace(steps_deep)[-1].state
            # randomly generate missing fluents according to the size of the partial state/subset specified
            del_f = list(state.fluents.keys())
            random.shuffle(del_f)
            del_f = del_f[: int(len(state.fluents) * (1 - subset_size_perc))]
            # delete the missing fluents
            for f in del_f:
                del state.fluents[f]
            goal_states.add(state)
        return goal_states
