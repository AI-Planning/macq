import random
from typing import Dict
from tarski.model import create
from collections import OrderedDict
from . import VanillaSampling
from ...trace import TraceList, State
from ...observation.partial_observation import PercentError
from ...utils.timer import basic_timer



MAX_GOAL_SEARCH_TIME = 30.0


class RandomGoalSampling(VanillaSampling):
    def __init__(
        self,
        new_domain: str,
        new_prob: str,
        steps_deep: int,
        enforced_hill_climbing_sampling: bool = True,
        subset_size_perc: int = 1,
        num_traces: int = 1,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
    ):
        if subset_size_perc < 0 or subset_size_perc > 1:
            raise PercentError()
        self.new_domain = new_domain
        self.new_prob = new_prob
        self.steps_deep = steps_deep
        self.subset_size_perc = subset_size_perc
        self.num_traces = num_traces
        self.enforced_hill_climbing_sampling = enforced_hill_climbing_sampling
        super().__init__(dom=dom, prob=prob, problem_id=problem_id, num_traces=num_traces)

    def goal_sampling(self):
        goal_states = {}
        self.generate_goals(goal_states=goal_states)
        # sort the results by plan length and get the k largest ones
        filtered_goals = OrderedDict(sorted(goal_states.items(), key=lambda x : len(x[1].actions)))
        to_del = list(filtered_goals.keys())[:len(filtered_goals) - self.num_traces]
        for d in to_del:
            del filtered_goals[d]
        return filtered_goals

    @basic_timer(num_seconds=MAX_GOAL_SEARCH_TIME)
    def generate_goals(self, goal_states: Dict):
        # create a sampler to test the complexity of the new goal by running a planner on it
        # test_plan_complexity_sampler = VanillaSampling(
        #     dom=self.pddl_dom, prob=self.pddl_prob, problem_id=self.problem_id
        # )
        #test_plan_complexity_sampler = self
        k_length_plans = 0
        while True:
            # generate a trace of the specified length and retrieve the state of the last step
            state = self.generate_single_trace(self.steps_deep)[-1].state

            # get all positive fluents (only positive fluents can be used for a goal)
            pos_f = [f for f in state if state[f]]
            # get the subset size
            subset_size = int(len(state.fluents) * self.subset_size_perc)
            # if necessary, take a subset of the fluents
            if len(pos_f) > subset_size:
                random.shuffle(pos_f)
                pos_f = pos_f[:subset_size]

            self.change_goal(
                goal_fluents=pos_f, new_domain=self.new_domain, new_prob=self.new_prob
            )

            # ensure that the goal doesn't hold in the initial state; restart if it does
            init_state = {
                str(a) for a in self.problem.init.as_atoms()
            }
            goal = {
                str(a) for a in self.problem.goal.subformulas
            }
            # print(init_state)
            # print(goal)
            # print()
            if goal.issubset(init_state):
                continue

            try:
                # attempt to generate a plan, and find a new goal if a plan can't be found
                test_plan = self.generate_plan()
            except KeyError as e:
                continue

            # optionally change the initial state of the sampler to the goal just generated (ensures more diversity in goals/plans)
            if self.enforced_hill_climbing_sampling:
                init = create(self.lang)
                for a in self.problem.goal.subformulas:
                    init.add(a.predicate, *a.subterms)
                self.problem.init = init

            # create a State and add it to the dictionary
            state_dict = {}
            for f in pos_f:
                state_dict[f] = True
            goal_states[State(state_dict)] = test_plan
            # keep track of the number of plans of length k; if we get enough of them, exit early
            if len(test_plan.actions) >= self.steps_deep:
                k_length_plans += 1
            if k_length_plans >= self.num_traces:
                 break
            

    def generate_traces(self):
        traces = TraceList()
        # retrieve goals and their respective plans
        goals_w_plans = self.goal_sampling()
        # store the goals so that the sampler goal can be reverted/changed if needed
        # TODO: store goals as sets of fluents
        self.goals = list(goals_w_plans.keys())
        # iterate through all plans corresponding to the goals, generating traces
        for plan in goals_w_plans.values():
            # generate a plan based on the new goal, then generate a trace based on that plan
            traces.append(
                self.generate_single_trace_from_plan(plan)
            )
        return traces