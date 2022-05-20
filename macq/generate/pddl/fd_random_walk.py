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

class FDRandomWalkSampling(Generator):
    """Random Walk Sampler -- inherits from the VanillaSampling base class.

    Follows the method laid out in the FastDownward planning system for conducting state samples:
    - https://github.com/aibasel/downward/blob/main/src/search/task_utils/sampling.cc

    Taken from the FastDownward planning system:
        The walk length is taken from a binomial distribution centered around the
        estimated plan length, which is computed as the ratio of the h value of
        the initial state divided by the average operator costs. Whenever a dead
        end is detected or a state has no successors, restart from the initial
        state. The function 'is_dead_end' should return whether a given state is
        a dead end. If omitted, no dead end detection is performed. The 'init_h'
        value should be an estimate of the solution cost.

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
        max_time: float = 30,
        init_h: int = None,
        num_traces: int = 1,
        seed: int = None,
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
            num_traces=num_traces,
            max_time=max_time,
        )

        self.init_h = init_h
        self.traces = self.generate_traces()

    def generate_traces(self):
        """Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Returns:
            A TraceList object with the list of traces generated.
        """
        traces = TraceList()
        traces.generator = self.generate_single_trace_setup(num_seconds=self.max_time)
        for _ in print_progress(range(self.num_traces)):
            traces.append(traces.generator())
        return traces

    def plan_len(self):
        """Samples the target plan length from the heuristic value"""
        return 42
