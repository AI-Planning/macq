
import random

from . import VanillaSampling

class FDRandomWalkSampling(VanillaSampling):
    """Random Walk Sampler -- inherits from the VanillaSampling base class.

    Follows the method laid out in the FastDownward planning system for conducting state samples:
    - https://github.com/aibasel/downward/blob/main/src/search/task_utils/sampling.cc

    Taken from the FastDownward planning system:
        The walk length is taken from a binomial distribution centered around the
        estimated plan length, which is computed as the ratio of the h value of
        the initial state divided by the average operator costs. Whenever a dead
        end is detected or a state has no successors, restart from the initial
        state. The 'init_h' value should be an estimate of the solution cost.

    Attributes:
        max_time(float):
            The maximum time allowed for a trace to be generated.
        init_h(int):
            Initial estimate of the cost to the goal.
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
        max_time: float = 30,
        init_h: int = None,
        num_traces: int = 1,
        seed: int = None,
    ):
        """
        Initializes a the fd random walk sampler.

        Args:
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
            observe_pres_effs (bool):
                Option to observe action preconditions and effects upon generation.
            max_time (float):
                The maximum time allowed for a trace to be generated.
            init_h (int):
                The estimated initial heuristic value. Defaults to 10.
            num_traces (int):
                The number of traces to generate. Defaults to 1.
            seed (int):
                The seed for the random number generator.
        """

        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
            observe_pres_effs=observe_pres_effs,
            ignore_static_fluents=ignore_static_fluents,
            num_traces=num_traces,
            seed=seed,
            max_time=max_time,
        )

        if init_h is None:
            self.init_h = 10
        else:
            # From the FastDownward planning system:
            #
            #   Convert heuristic value into an approximate number of actions
            #   (does nothing on unit-cost problems).
            #
            #   The expected walk length is np = 2 * estimated number of solution steps.
            #   (We multiply by 2 because the heuristic is underestimating.)
            avg_op_cost = self._avg_op_cost()
            assert avg_op_cost > 0, "Average operator cost must be greater than 0"
            sol_steps = int((init_h / avg_op_cost) * 0.5)
            self.init_h = 4 * sol_steps

        self.plan_len = self._plan_len
        self.traces = self.generate_traces()

    def _plan_len(self):
        """Samples the target plan length from the heuristic value"""

        p = 0.5

        # Length is based on the binomial distribution
        depth = 0
        for i in range(self.init_h):
            if random.random() < p:
                depth += 1
        return depth

    def _avg_op_cost(self):
        """Computes the average operator cost"""

        def _op_cost(a):
            if self.problem.get_action(a).cost is None:
                return 1
            else:
                return float(self.problem.get_action(a).cost.symbol)

        costs = {a: _op_cost(a) for a in self.problem.actions}
        total = 0
        for o in self.instance.operators:
            total += costs[o.name.split('(')[0]]
        return total / len(self.instance.operators)
