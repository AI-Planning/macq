from .generator import Generator


class TraceFromGoal(Generator):
    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        observe_pres_effs: bool = False,
        ignore_static_fluents: bool = True,  # defaults to true to not break any pre-implemented scripts

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
            observe_pres_effs (bool):
                Option to observe action preconditions and effects upon generation.
        """
        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
            observe_pres_effs=observe_pres_effs,
            ignore_static_fluents=ignore_static_fluents
        )
        self.trace = self.generate_trace()

    def generate_trace(self):
        self.trace = self.generate_single_trace_from_plan(self.generate_plan())
        return self.trace
