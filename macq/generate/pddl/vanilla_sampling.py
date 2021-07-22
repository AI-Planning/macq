from tarski.model import create
from tarski.search.operations import progress
from typing import Dict
import random
from . import Generator
from ...utils.timer import set_timer_throw_exc, TraceSearchTimeOut, basic_timer
from ...utils.trace_utils import set_num_traces, set_plan_length
from ...observation.partial_observation import PercentError
from ...trace import (
    Step,
    State,
    Trace,
    TraceList,
)


MAX_TRACE_TIME = 30.0
MAX_GOAL_SEARCH_TIME = 60.0


class VanillaSampling(Generator):
    """Vanilla State Trace Sampler - inherits the base Generator class and its attributes.

    A basic state trace generator that Generates traces randomly by uniformly sampling applicable actions to find plans
    of the given length.

    Attributes:
        plan_len (int):
            The length of the traces to be generated.
        num_traces (int):
            The number of traces to be generated.
        traces (TraceList):
            The list of traces generated.
    """

    def __init__(
        self,
        plan_len: int = 0,
        num_traces: int = 0,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        seed: int = None,
    ):
        """
        Initializes a vanilla state trace sampler using the plan length, number of traces,
        and the domain and problem.

        Args:
            plan_len (int):
                The length of each generated trace. Defaults to 0 (in case the sampler is only being used for goal sampling).
            num_traces (int):
                The number of traces to generate. Defaults to 0 (in case the sampler is only being used for goal sampling).
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
        if seed:
            random.seed(seed)

    def generate_traces(self):
        """Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Returns:
            A TraceList object with the list of traces generated.
        """
        traces = TraceList()
        traces.generator = self.generate_single_trace
        for _ in range(self.num_traces):
            traces.append(self.generate_single_trace())
        return traces

    @set_timer_throw_exc(num_seconds=MAX_TRACE_TIME, exception=TraceSearchTimeOut)
    def generate_single_trace(self, plan_len: int = None):
        """Generates a single trace using the uniform random sampling technique.
        Loops until a valid trace is found. Wrapper does not allow the function
        to run past the time specified by the time specified.

        Returns:
            A Trace object (the valid trace generated).
        """

        if not plan_len:
            plan_len = self.plan_len

        trace = Trace()

        state = self.problem.init
        valid_trace = False
        while not valid_trace:
            trace.clear()
            # add more steps while the trace has not yet reached the desired length
            for j in range(plan_len):
                # if we have not yet reached the last step
                if len(trace) < plan_len - 1:
                    # find the next applicable actions
                    app_act = list(self.instance.applicable(state))
                    # if the trace reaches a dead lock, disregard this trace and try again
                    if not app_act:
                        break
                    # pick a random applicable action and apply it
                    act = random.choice(app_act)
                    # create the trace and progress the state
                    macq_action = self.tarski_act_to_macq(act)
                    macq_state = self.tarski_state_to_macq(state)
                    step = Step(macq_state, macq_action, j + 1)
                    trace.append(step)
                    state = progress(state, act)
                else:
                    macq_state = self.tarski_state_to_macq(state)
                    step = Step(state=macq_state, action=None, index=j + 1)
                    trace.append(step)
                    valid_trace = True
        return trace

    def goal_sampling(
        self,
        new_domain: str,
        new_prob: str,
        num_states: int,
        steps_deep: int,
        time_limit: float = MAX_GOAL_SEARCH_TIME,
        subset_size_perc: int = 1,
        enforced_hill_climbing_sampling: bool = True,
    ):
        if subset_size_perc < 0 or subset_size_perc > 1:
            raise PercentError()
        goal_states = {}

        self.MAX_GOAL_SEARCH_TIME = time_limit
        self.generate_goals(
            new_domain=new_domain,
            new_prob=new_prob,
            steps_deep=steps_deep,
            subset_size_perc=subset_size_perc,
            enforced_hill_climbing_sampling=enforced_hill_climbing_sampling,
            goal_states=goal_states,
        )

        return goal_states

    @basic_timer(num_seconds=MAX_GOAL_SEARCH_TIME)
    def generate_goals(
        self,
        new_domain: str,
        new_prob: str,
        steps_deep: int,
        subset_size_perc: int,
        enforced_hill_climbing_sampling: bool,
        goal_states: Dict,
    ):
        # create a sampler to test the complexity of the new goal by running a planner on it
        test_plan_complexity_sampler = VanillaSampling(
            dom=self.pddl_dom, prob=self.pddl_prob, problem_id=self.problem_id
        )
        while True:
            # generate a trace of the specified length and retrieve the state of the last step
            state = self.generate_single_trace(steps_deep)[-1].state

            # get all positive fluents (only positive fluents can be used for a goal)
            pos_f = [f for f in state if state[f]]
            # get the subset size
            subset_size = int(len(state.fluents) * subset_size_perc)
            # if necessary, take a subset of the fluents
            if len(pos_f) > subset_size:
                random.shuffle(pos_f)
                pos_f = pos_f[:subset_size]

            test_plan_complexity_sampler.change_goal(
                goal_fluents=pos_f, new_domain=new_domain, new_prob=new_prob
            )

            # ensure that the goal doesn't hold in the initial state; restart if it does
            init_state = {
                str(a) for a in test_plan_complexity_sampler.problem.init.as_atoms()
            }
            goal = {
                str(a) for a in test_plan_complexity_sampler.problem.goal.subformulas
            }
            print(init_state)
            print(goal)
            print()
            if goal.issubset(init_state):
                continue

            try:
                # attempt to generate a plan, and find a new goal if a plan can't be found
                test_plan = test_plan_complexity_sampler.generate_plan()
            except KeyError as e:
                continue

            # optionally change the initial state of the sampler to the goal just generated (ensures more diversity in goals/plans)
            if enforced_hill_climbing_sampling:
                init = create(test_plan_complexity_sampler.lang)
                for a in test_plan_complexity_sampler.problem.goal.subformulas:
                    init.add(a.predicate, *a.subterms)
                test_plan_complexity_sampler.problem.init = init

            # create a State and add it to the set
            state_dict = {}
            for f in pos_f:
                state_dict[f] = True
            goal_states[State(state_dict)] = test_plan
