from . import VanillaSampling, Generator


class RandomGoalSampling(Generator):
    def __init__(
        self,
        steps_deep: int,
        subset_size_perc: int,
        num_traces: int = 1,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
    ):
        self.vanilla_gen = VanillaSampling(dom=dom, prob=prob)
        self.traces = self.generate_traces()

    def generate_traces(self):
        # retrieve goals and ensure that "bad"/easy goals are tossed out (do this in the goal sampling function)
        # store the goals so that the sampler goal can be reverted/changed if needed
        self.goals = self.vanilla_gen.goal_sampling(
            self.num_traces, self.steps_deep, self.subset_size_perc
        )
        # iterate through all goals, changing the generator's goal to the current goal each iteration
        # generating a plan based on the new goal with generate_plan
        # generate a trace from that plan with generate_single_trace_from_plan
        # repeat for all goals.
