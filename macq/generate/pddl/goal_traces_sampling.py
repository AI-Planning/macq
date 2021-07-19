from tarski.search.operations import progress
from tarski.fstrips.action import PlainOperator
from typing import List
import random
from .generator import Generator
from .plan import Plan
from ...utils.trace_utils import set_num_traces, set_plan_length
from ...utils.timer import set_timer, TraceSearchTimeOut, PlanSearchTimeOut
from ...trace import Trace, TraceList, Step

MAX_TRACE_TIME = 30.0
MAX_PLAN_TIME = 30.0


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
        self.plan_len = set_plan_length(plan_len) if plan_len else None
        self.num_traces = set_num_traces(num_traces)
        self.plans = set()
        self.traces = self.generate_traces()

    def generate_traces(self):
        traces = TraceList()
        while len(traces) < self.num_traces:
            try:
                traces.append(self.generate_single_trace(self.generate_unique_plan()))
            except PlanSearchTimeOut as e:
                print(e)
                print(
                    "WARNING: Only the first "
                    + str(len(traces))
                    + " trace(s) are unique. The rest will be duplicates."
                )
                while len(traces) < self.num_traces:
                    # instead of regenerating a plan, randomly select an existing plan for efficiency
                    traces.append(
                        self.generate_single_trace(random.choice(tuple(self.plans)))
                    )
        return traces

    @set_timer(num_seconds=MAX_PLAN_TIME, exception=PlanSearchTimeOut)
    # function to generate a single plan - also timed.
    def generate_unique_plan(self):
        duplicate = True
        while duplicate:
            plan = self.generate_plan(self.plan_len)
            duplicate = plan in self.plans
            if not duplicate:
                self.plans.add(plan)
                return plan

    @set_timer(num_seconds=MAX_TRACE_TIME, exception=TraceSearchTimeOut)
    def generate_single_trace(self, plan: Plan):
        trace = Trace()
        trace.clear()
        actions = plan.actions

        # get initial state
        state = self.problem.init
        # note that we add 1 because the states represented take place BEFORE their subsequent action,
        # so if we need to take x actions, we need x + 1 states and therefore x + 1 steps in the trace.
        for i in range(self.plan_len + 1):
            macq_state = self.tarski_state_to_macq(state)
            # if we have not yet reached the end of the trace
            if len(trace) < self.plan_len:
                act = actions[i]
                trace.append(Step(macq_state, self.tarski_act_to_macq(act), i + 1))
                state = progress(state, act)
            else:
                trace.append(Step(macq_state, None, i + 1))
        return trace
