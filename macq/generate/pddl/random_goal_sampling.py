from . import VanillaSampling, Generator
from ...trace import TraceList


class RandomGoalSampling(Generator):
    def __init__(
        self,
        steps_deep: int,
        plan_complexity: int,
        subset_size_perc: int = 1,
        num_traces: int = 1,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
    ):
        super().__init__(dom=dom, prob=prob, problem_id=problem_id)
        self.vanilla_gen = VanillaSampling(dom=dom, prob=prob)
        self.steps_deep = steps_deep
        self.plan_complexity = plan_complexity
        self.subset_size_perc = subset_size_perc
        self.num_traces = num_traces
        self.traces = self.generate_traces()

    def generate_traces(self):
        traces = TraceList()
        # store the goals so that the sampler goal can be reverted/changed if needed
        self.goals = self.vanilla_gen.goal_sampling(
            num_states=self.num_traces,
            steps_deep=self.steps_deep,
            plan_complexity=self.plan_complexity,
            subset_size_perc=self.subset_size_perc,
        )
        # iterate through all goals, changing the generator's goal to the current goal each iteration
        for state in self.goals:
            pos_f = {f for f in state if state[f]}
            neg_f = {f for f in state if not state[f]}
            self.vanilla_gen.change_goal(pos_f, neg_f)
            # generate a plan based on the new goal, then generate a trace based on that plan
            traces.append(
                self.generate_single_trace_from_plan(self.vanilla_gen.generate_plan())
            )
        return traces
