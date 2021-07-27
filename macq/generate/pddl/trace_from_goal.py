from .generator import Generator


class TraceFromGoal(Generator):
    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
    ):
        """
        Initializes a goal state trace sampler using the domain and problem. This method of sampling
        takes the goal of the problem into account and uses a generated plan to generate a trace.

        Args:
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
        """
        super().__init__(dom=dom, prob=prob, problem_id=problem_id)
        self.trace = self.generate_trace()

    def generate_trace(self):
        return self.generate_single_trace_from_plan(self.generate_plan())
