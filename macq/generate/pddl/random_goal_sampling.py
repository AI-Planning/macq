import random
from typing import Dict
from tarski.syntax.formulas import Atom
from collections import OrderedDict
from . import VanillaSampling
from ...trace import TraceList, State
from ...observation.partial_observation import PercentError
from ...utils.timer import basic_timer



MAX_GOAL_SEARCH_TIME = 30.0


class RandomGoalSampling(VanillaSampling):
    def __init__(
        self,
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
        self.steps_deep = steps_deep
        self.subset_size_perc = subset_size_perc
        self.num_traces = num_traces
        self.enforced_hill_climbing_sampling = enforced_hill_climbing_sampling
        self.goals = []
        super().__init__(dom=dom, prob=prob, problem_id=problem_id, num_traces=num_traces)

    def goal_sampling(self):
        goal_states = {}
        self.generate_goals(goal_states=goal_states)
        # sort the results by plan length and get the k largest ones
        filtered_goals = OrderedDict(sorted(goal_states.items(), key=lambda x : len(x[1]["plan"].actions)))
        to_del = list(filtered_goals.keys())[:len(filtered_goals) - self.num_traces]
        for d in to_del:
            del filtered_goals[d]
        return filtered_goals

    @basic_timer(num_seconds=MAX_GOAL_SEARCH_TIME)
    def generate_goals(self, goal_states: Dict):
        # create a sampler to test the complexity of the new goal by running a planner on it
        k_length_plans = 0
        while True:
            # generate a trace of the specified length and retrieve the state of the last step
            state = self.generate_single_trace(self.steps_deep)[-1].state

            # get all positive fluents (only positive fluents can be used for a goal)
            goal_f = [f for f in state if state[f]]
            # get next initial state (only used for enforced hill climbing sampling)
            next_init_f = goal_f.copy()
            # get the subset size
            subset_size = int(len(state.fluents) * self.subset_size_perc)
            # if necessary, take a subset of the fluents
            if len(goal_f) > subset_size:
                random.shuffle(goal_f)
                goal_f = goal_f[:subset_size]

            self.change_goal(goal_fluents=goal_f)

            # ensure that the goal doesn't hold in the initial state; restart if it does
            init_state = {
                str(a) for a in self.problem.init.as_atoms()
            }
            goal = {
                str(a) for a in self.problem.goal.subformulas
            }

            if goal.issubset(init_state):
                continue

            try:
                # attempt to generate a plan, and find a new goal if a plan can't be found
                # should only crash if there are server issues
                test_plan = self.generate_plan()
            except KeyError as e:
                continue

            # create a State and add it to the dictionary
            state_dict = {}
            for f in goal_f:
                state_dict[f] = True
            # map each goal to the initial state and plan used to achieve it
            goal_states[State(state_dict)] = {"plan": test_plan, "initial state": self.problem.init}

            # optionally change the initial state of the sampler for the next iteration to the goal state just generated (ensures more diversity in goals/plans)
            # use the full state the goal was extracted from as the initial state to prevent planning errors from incomplete initial states
            if self.enforced_hill_climbing_sampling:
                self.change_init(next_init_f)

            # keep track of the number of plans of length k; if we get enough of them, exit early
            if len(test_plan.actions) >= self.steps_deep:
                k_length_plans += 1
            if k_length_plans >= self.num_traces:
                 break
            

    def generate_traces(self):
        traces = TraceList()
        # retrieve goals and their respective plans
        goals_w_plans = self.goal_sampling()
        # store the goals as sets of fluents so that the sampler goal can be reverted/changed if needed
        goals = list(goals_w_plans.keys())
        self.goals.extend([{f for f in state} for state in goals])
        # iterate through all plans corresponding to the goals, generating traces
        for goal in goals_w_plans.values():
            # update the initial state if necessary
            if self.enforced_hill_climbing_sampling:
                self.problem.init = goal["initial state"]
            # generate a plan based on the new goal/initial state, then generate a trace based on that plan
            traces.append(
                self.generate_single_trace_from_plan(goal["plan"])
            )
        return traces