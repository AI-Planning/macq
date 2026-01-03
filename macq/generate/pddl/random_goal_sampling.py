import random
from collections import OrderedDict
from typing import Dict
from . import VanillaSampling
from ...trace import TraceList, State
from ...utils import PercentError, basic_timer, progress


class RandomGoalSampling(VanillaSampling):
    """Random Goal State Trace Sampler - inherits the VanillaSampling class and its attributes.

    A state trace generator that generates traces by randomly generating some candidate states/goals k steps deep,
    then running a planner on a random subset of the fluents to get plans. The longest plans (those closest to k, thus representing
    goal states that are somewhat complex and take longer to reach) are taken and used to generate traces.

    Attributes:
        steps_deep (int):
            The number of steps deep to extract goal states from.
        enforced_hill_climbing_sampling (bool):
            Optional method of goal sampling where once a goal is found, that (full) goal state is set as the initial state for the next
            iteration. This results in more unique goals as the goal state sampling starts in different areas of the state space each time.
            Note that the goals will come from different initial states.
        subset_size_perc (float):
            The percentage of fluents to extract to use as a goal state from the generated states.
        goals_inits_plans (List[Dict]):
            A list of dictionaries, where each dictionary stores the generated goal state as the key and the initial state and plan used to
            reach the goal as values.
    """

    def __init__(
        self,
        steps_deep: int,
        enforced_hill_climbing_sampling: bool = True,
        subset_size_perc: float = 1,
        num_traces: int = 0,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        max_time: float = 30,
        observe_pres_effs: bool = False,
        ignore_static_fluents: bool = True,  # defaults to true to not break any pre-implemented scripts
    ):
        """
        Initializes a random goal state trace sampler using the plan length, number of traces,
        and the domain and problem.

        Args:
            steps_deep (int):
                The number of steps deep to extract goal states from.
            enforced_hill_climbing_sampling (bool):
                Optional method of goal sampling where once a goal is found, that (full) goal state is set as the initial state for the next
                iteration. This results in more unique goals as the goal state sampling starts in different areas of the state space each time.
                Note that the goals will come from different initial states.
            subset_size_perc (float):
                The percentage of fluents to extract to use as a goal state from the generated states.
            num_traces (int):
                The number of traces to generate. Defaults to 1.
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
            max_time (float):
                The maximum time allowed for a trace to be generated.
            observe_pres_effs (bool):
                Option to observe action preconditions and effects upon generation.
        """
        if subset_size_perc < 0 or subset_size_perc > 1:
            raise PercentError()
        self.steps_deep = steps_deep
        self.enforced_hill_climbing_sampling = enforced_hill_climbing_sampling
        self.subset_size_perc = subset_size_perc
        self.goals_inits_plans = []
        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
            num_traces=num_traces,
            observe_pres_effs=observe_pres_effs,
            ignore_static_fluents=ignore_static_fluents,
            max_time=max_time,
        )

    def goal_sampling(self):
        """Samples goals by randomly generating candidate goal states k (`steps_deep`) steps deep, then running planners on those
        goal states to ensure the goals are complex enough (i.e. cannot be reached in too few steps). Candidate
        goal states are generated for a set amount of time indicated by MAX_GOAL_SEARCH_TIME, and the goals with the
        longest plans (the most complex goals) are selected.

        Returns: An OrderedDict holding the longest goal states along with the initial state and plans used to reach them.
        """
        goal_states = {}
        self.generate_goals_setup(num_seconds=self.max_time, goal_states=goal_states)()
        # sort the results by plan length and get the k largest ones
        filtered_goals = OrderedDict(
            sorted(goal_states.items(), key=lambda x: len(x[1]["plan"].actions))
        )
        to_del = list(filtered_goals.keys())[: len(filtered_goals) - self.num_traces]
        for d in to_del:
            del filtered_goals[d]
        return filtered_goals

    def generate_goals_setup(self, num_seconds: float, goal_states: Dict):
        @basic_timer(num_seconds=num_seconds)
        def generate_goals(self=self, goal_states=goal_states):
            """Helper function for `goal_sampling`. Generates as many goals as possible within the specified max_time seconds (timing is
            enforced by the basic_timer wrapper).

            The outside function is a wrapper that provides parameters for both the timer
            wrapper and the function.

            Given the specified number of traces `num_traces`, if `num_traces` plans of length k (`steps_deep`) are found before
            the time is up, exit early.

            Args:
                goal_states (Dict):
                    The dictionary to fill with the values of each goal state, initial state, and plan.
            """
            # create a sampler to test the complexity of the new goal by running a planner on it
            k_length_plans = 0
            while True:
                # generate a trace of the specified length and retrieve the state of the last step
                state = self.generate_single_trace_setup(
                    num_seconds, self.steps_deep
                )()[-1].state

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
                init_state = {str(a) for a in self.problem.init.as_atoms()}
                goal = {str(a) for a in self.problem.goal.subformulas}

                if goal.issubset(init_state):
                    continue

                try:
                    # attempt to generate a plan, and find a new goal if a plan can't be found
                    # should only crash if there are server issues
                    test_plan = self.generate_plan()
                except KeyError:
                    continue

                # create a State and add it to the dictionary
                state_dict = {}
                for f in goal_f:
                    state_dict[f] = True
                # map each goal to the initial state and plan used to achieve it
                goal_states[State(state_dict)] = {
                    "plan": test_plan,
                    "initial state": self.problem.init,
                }

                # optionally change the initial state of the sampler for the next iteration to the goal state just generated (ensures more diversity in goals/plans)
                # use the full state the goal was extracted from as the initial state to prevent planning errors from incomplete initial states
                if self.enforced_hill_climbing_sampling:
                    self.change_init(next_init_f)

                # keep track of the number of plans of length k; if we get enough of them, exit early
                if len(test_plan.actions) >= self.steps_deep:
                    k_length_plans += 1
                if k_length_plans >= self.num_traces:
                    break

        return generate_goals

    def generate_traces(self):
        """Generates traces based on the sampled goals. Traces are generated using the initial state and plan used to achieve the goal.

        Returns:
            A TraceList with the generated traces.
        """
        traces = TraceList()
        # retrieve goals and their respective plans
        self.goals_inits_plans = self.goal_sampling()
        # iterate through all plans corresponding to the goals, generating traces
        for goal in progress(self.goals_inits_plans.values()):
            # update the initial state if necessary
            if self.enforced_hill_climbing_sampling:
                self.problem.init = goal["initial state"]
            # generate a plan based on the new goal/initial state, then generate a trace based on that plan
            traces.append(self.generate_single_trace_from_plan(goal["plan"]))
        self.traces = traces
        return traces
