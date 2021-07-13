from tarski.search.operations import progress
from .generator import Generator
from ...utils.trace_utils import set_num_traces, set_plan_length
from ...trace import Trace, Step


class GoalTracesSampling(Generator):
    def __init__(
        self,
        plan_len: int = None,
        num_traces: int = 1,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
    ):
        """
        Initializes a goal state trace sampler using the plan length, number of traces,
        and the domain and problem. This method of sampling takes the goal of the problem
        into account and uses a generated plan to generate its traces.

        Args:
            plan_len (int):
                The length of each generated trace. (If not specified/None, the plan length
                will default to the length of the generated plan. Note that the plan length supplied,
                if too short, may result in a trace that does not reach the goal).
            num_traces (int):
                The number of traces to generate. Defaults to 1.
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

    # TODO: separate into a generate_single_trace function and add the timer
    def generate_traces(self):
        trace = Trace()
        for _ in range(self.num_traces):
            plan = self.generate_plan()
            # if the plan length is longer than the generated plan, just use the plan length
            if self.plan_len > len(plan):
                self.plan_len = len(plan)
            state = self.problem.init
            for i in range(self.plan_len):
                macq_state = self.tarski_state_to_macq(state)
                if i < self.plan_len - 1:
                    act = plan[i]
                    macq_action = self.tarski_act_to_macq(act)
                    step = Step(macq_state, macq_action, i + 1)
                else:
                    step = Step(macq_state, None, i + 1)
                trace.append(step)
                state = progress(state, act)
            print()

            # do the following for however many TRACES they specified
            # generate the plan (list of TARSKI actions)
            # truncate the plan list if necessary, according to the plan length provided.
            # start at the initial state
            # iterate through all actions and progress the state, generating a macq Trace as you go along.
