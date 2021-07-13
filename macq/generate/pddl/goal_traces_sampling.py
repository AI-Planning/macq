from macq.generate.trace_utils import set_num_traces, set_plan_length


class GoalTracesSampling(Generator):
    def __init__(
        self,
        plan_len: int,
        num_traces: int,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
    ):
        """
        Initializes a goal state trace sampler using the plan length, number of traces,
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

    def generate_traces(self):
        pass
