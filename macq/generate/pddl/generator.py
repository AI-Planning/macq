from time import sleep
from typing import Iterable, List, Optional, Set, Tuple, Union

import pddlutils as pu
import requests
from pddl import parse_domain, parse_problem
from pddl.action import Action as GroundAction
from pddl.core import Problem
from pddl.logic import Predicate
from pddl.logic.base import And
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from pddlutils.strips import get_precondition, get_strips_literal_list

from .planning_domains_api import get_problem, get_plan
from ..plan import Plan
from ...trace import Action, State, PlanningObject, Fluent, Trace, Step


class PlanningDomainsAPIError(Exception):
    """Raised when a valid response cannot be obtained from the planning.domains solver."""

    def __init__(self, message):
        super().__init__(message)


class InvalidGoalFluent(Exception):
    """
    Raised when the user attempts to supply a new goal with invalid fluent(s).
    """

    def __init__(self, fluent, message=None):
        if message is None:
            message = f"{fluent} is not available in this problem."
        super().__init__(message)


class InvalidPlanStep(Exception):
    """Raised when a step of a plan does not name a ground action of the problem."""

    def __init__(self, step, message=None):
        if message is None:
            message = f"{step} is not a ground action of this problem."
        super().__init__(message)


class Generator:
    """A Generator.

    A basic PDDL state trace generator. Handles all parsing and stores the domain,
    problem, and planning task for the child generators to easily access and use.

    Supports the PDDL fragment of pddl-utils: `:strips`, `:typing`,
    `:negative-preconditions` and `:equality`.

    Attributes:
        pddl_dom (str):
            The name of the local PDDL domain filename (relevant if the problem ID is not provided.)
        pddl_prob (str):
            The name of the local PDDL problem filename (relevant if the problem ID is not provided.)
        problem_id (int):
            The ID of the problem to be accessed (relevant if local files are not provided.)
        domain (pddl.core.Domain):
            The domain definition.
        problem (pddl.core.Problem):
            The problem definition.
        task (pddlutils.Task):
            The planning task, which provides the state semantics.
        grounded_fluents (list):
            Every type-consistent ground atom of the problem, in the form of macq Fluents.
            Atoms of predicates no action changes are left out if `ignore_static_fluents` is set.
        observe_pres_effs (bool):
            Option to observe action preconditions and effects upon generation.
    """

    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        observe_pres_effs: bool = False,
        ignore_static_fluents: bool = True # defaults to true to not break any pre-implemented scripts that
           # did not consider this argument.
    ):
        """Creates a basic PDDL state trace generator. Takes either the raw filenames
        of the domain and problem or a problem ID.

        Args:
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
            observe_pres_effs (bool):
                Option to observe action preconditions and effects upon generation.
            ignore_static_fluents (bool): option to ignore static fluents when generating traces. (default: True)

        Raises:
            NotImplementedError:
                Raised if the domain or problem is outside the supported PDDL fragment.
        """
        # get attributes
        self.ignore_static_fluents = ignore_static_fluents
        self.pddl_dom = dom
        self.pddl_prob = prob
        self.problem_id = problem_id
        self.observe_pres_effs = observe_pres_effs
        # read the domain and problem
        if not problem_id:
            self.domain = parse_domain(str(dom))
            self.problem = parse_problem(str(prob))
        else:
            urls = get_problem(problem_id, formalism='classical')
            self.domain = DomainParser()(requests.get(urls["domain_url"]).text)
            self.problem = ProblemParser()(requests.get(urls["problem_url"]).text)
        self.task = pu.Task(self.domain, self.problem)

        self._objects = {str(obj.name): obj for obj in self.task.objects}
        self._planning_objects = {
            name: PlanningObject(str(obj.type_tag or "object"), name)
            for name, obj in self._objects.items()
        }
        self._changing_predicates = self.__get_changing_predicates()
        self.grounded_fluents = self.__get_all_grounded_fluents()
        self._fluent_keys = {self._fluent_key(f) for f in self.grounded_fluents}

    def extract_action_typing(self):
        """Retrieves a dictionary mapping all of this problem's actions and the types
        of objects they act upon.

        i.e., given the standard blocks problem/domain, this function would return:
        {'pick-up': ['object'], 'put-down': ['object'], 'stack': ['object', 'object'],
        'unstack': ['object', 'object']}

        Returns:
            The dictionary that indicates the types of all the objects each action in
            the problem acts upon.
        """
        return {
            str(action.name): [_type_name(term) for term in action.parameters]
            for action in self.domain.actions
        }

    def extract_predicate_typing(self):
        """Retrieves a dictionary mapping all of this problem's predicates and the types
        of objects they act upon.

        i.e., given the standard blocks problem/domain, this function would return:
        {'on': ['object', 'object'], 'ontable': ['object'], 'clear': ['object'],
        'handempty': [], 'holding': ['object']}

        Returns:
            The dictionary that indicates the types of all the objects each predicate in
            the problem acts upon.
        """
        return {
            str(predicate.name): [_type_name(term) for term in predicate.terms]
            for predicate in self.domain.predicates
        }

    def __get_changing_predicates(self) -> Set[str]:
        """Finds the predicates that some action adds or deletes.

        Returns:
            The names of the predicates that appear in an action's effects.
        """
        names = set()
        for action in self.domain.actions:
            adds, deletes = _split_effects(action)
            names.update(str(atom.name) for atom in adds + deletes)
        return names

    def __get_all_grounded_fluents(self) -> List[Fluent]:
        """Extracts all the grounded fluents in the problem.

        Returns:
            A list of all the grounded fluents in the problem, in the form of macq Fluents.
        """
        return [
            self._atom_to_fluent(atom)
            for atom in self.task.ground_atoms()
            if not self.ignore_static_fluents
            or str(atom.name) in self._changing_predicates
        ]

    def _atom_to_fluent(self, atom: Predicate) -> Fluent:
        """Converts a ground atom to a fluent as defined by macq.

        Args:
            atom (Predicate):
                The supplied ground atom.

        Returns:
            A fluent, defined using the macq Fluent class.
        """
        return Fluent(
            str(atom.name),
            [self._planning_objects[str(term.name)] for term in atom.terms],
        )

    def _fluent_to_atom(self, fluent: Fluent) -> Predicate:
        """Converts a macq fluent to a ground atom.

        Args:
            fluent (Fluent):
                The supplied fluent.

        Returns:
            The ground atom the fluent names.
        """
        return Predicate(fluent.name, *[self._objects[o.name] for o in fluent.objects])

    @staticmethod
    def _fluent_key(fluent: Fluent) -> Tuple[str, ...]:
        return (fluent.name, *[o.name for o in fluent.objects])

    def state_to_macq(self, state: Iterable[Predicate]) -> State:
        """Converts a set of true ground atoms to a state as defined by macq.

        Args:
            state (Iterable[Predicate]):
                The ground atoms that are true.

        Returns:
            A state, defined using the macq State class.
        """
        true_fluents = {self._fluent_key(self._atom_to_fluent(a)) for a in state}
        return State(
            {f: self._fluent_key(f) in true_fluents for f in self.grounded_fluents}
        )

    def action_to_macq(self, action: GroundAction) -> Action:
        """Converts a ground action to an action as defined by macq.

        A macq action can't mark a precondition as negative, so only the positive
        preconditions are recorded.

        Args:
            action (GroundAction):
                The supplied ground action.

        Returns:
            An action, defined using the macq Action class.
        """
        name = str(action.name)
        obj_params = [self._planning_objects[str(t.name)] for t in action.parameters]
        if not self.observe_pres_effs:
            return Action(name=name, obj_params=obj_params)

        precondition = get_precondition(action)
        conjuncts = getattr(precondition, "operands", (precondition,))
        adds, deletes = _split_effects(action)
        return Action(
            name=name,
            obj_params=obj_params,
            precond={
                self._atom_to_fluent(c) for c in conjuncts if isinstance(c, Predicate)
            },
            add={self._atom_to_fluent(atom) for atom in adds},
            delete={self._atom_to_fluent(atom) for atom in deletes},
        )

    def _replace_problem(self, init: Optional[Iterable] = None, goal=None):
        """Swaps the initial state or goal of the problem and rebuilds the task."""
        self.problem = Problem(
            self.problem.name,
            domain=self.domain,
            objects=self.problem.objects,
            init=self.problem.init if init is None else set(init),
            goal=self.problem.goal if goal is None else goal,
        )
        self.task = pu.Task(self.domain, self.problem)

    def _write_pddl(self, new_domain: str, new_prob: str):
        """Writes the current domain and problem, for later use by a planner."""
        with open(new_domain, "w") as domain_file:
            domain_file.write(str(self.domain))
        with open(new_prob, "w") as problem_file:
            problem_file.write(str(self.problem))
        self.pddl_dom = new_domain
        self.pddl_prob = new_prob

    def change_init(
        self,
        init_fluents: Union[Set[Fluent], List[Fluent]],
        new_domain: str = "new_domain.pddl",
        new_prob: str = "new_prob.pddl",
    ):
        """Changes the initial state of the `Generator`. The domain and problem PDDL files
        are rewritten to accomodate the new goal for later use by a planner.

        Static atoms are kept when the `Generator` ignores static fluents, because the
        caller has no way of supplying them.

        Parameters:
            init_fluents (Union[Set[Fluent], List[Fluent]]):
                The collection of fluents that will make up the new initial state.
            new_domain (str):
                The name of the new domain file.
            new_prob (str):
                The name of the new problem file.
        """
        init = {self._fluent_to_atom(f) for f in init_fluents}
        if self.ignore_static_fluents:
            init |= {
                atom
                for atom in self.task.initial_state
                if str(atom.name) not in self._changing_predicates
            }
        self._replace_problem(init=init)
        self._write_pddl(new_domain, new_prob)

    def change_goal(
        self,
        goal_fluents: Union[Set[Fluent], List[Fluent]],
        new_domain: str = "new_domain.pddl",
        new_prob: str = "new_prob.pddl",
    ):
        """Changes the goal of the `Generator`. The domain and problem PDDL files
        are rewritten to accomodate the new goal for later use by a planner.

        Args:
            goal_fluents (Union[Set[Fluent], List[Fluent]]):
                The collection of fluents that will make up the new goal.
            new_domain (str):
                The name of the new domain file.
            new_prob (str):
                The name of the new problem file.

        Raises:
            InvalidGoalFluent:
                Raised if any of the fluents supplied do not exist in this domain.
        """
        # check if the fluents to add are valid
        for f in goal_fluents:
            if self._fluent_key(f) not in self._fluent_keys:
                raise InvalidGoalFluent(f)

        self._replace_problem(goal=And(*[self._fluent_to_atom(f) for f in goal_fluents]))
        self._write_pddl(new_domain, new_prob)

    def _plan_step_to_action(self, step: str) -> GroundAction:
        """Finds the ground action a plan step names.

        Planners may lowercase names, so names match regardless of case unless that
        would be ambiguous.

        Args:
            step (str):
                The plan step, such as `(stack a b)`.

        Returns:
            The ground action.

        Raises:
            InvalidPlanStep:
                Raised if the step does not name a ground action of this problem.
        """
        words = step.strip("() \t").split()
        try:
            action_names = [str(action.name) for action in self.domain.actions]
            name = _match_name(words[0], action_names)
            objects = [_match_name(word, self._objects) for word in words[1:]]
            return self.task.ground(name, *objects)
        except (IndexError, KeyError, pu.PDDLLogicError) as error:
            raise InvalidPlanStep(step) from error

    def generate_plan(self, from_ipc_file: bool = False, filename: str = None) -> Plan | None:
        """Generates a plan. If reading from an IPC file, the `Plan` is read directly. Otherwise, if the initial state or
        goal was changed, these changes are taken into account through the updated PDDL files. If no changes were made, the
        default nitial state/goal in the initial problem file is used.

        Args:
            from_ipc_file (bool):
                Option to read a `Plan` from an IPC file instead of the `Generator`'s problem file. Defaults to False.
            filename (str):
                The name of the file to read the plan from.

        Returns:
            A `Plan` object that holds all the actions taken.

        Raises:
            InvalidPlanStep:
                Raised if a step of the plan does not name a ground action of this problem.
        """
        if not from_ipc_file:
            # if the files are only being generated from the problem ID and are unaltered, retrieve the existing plan (note that
            # if any changes were made, the local files would be used as the PDDL files are rewritten when changes are made).
            stored_plan = None
            if self.problem_id and not self.pddl_dom and not self.pddl_prob:
                stored_plan = get_plan(self.problem_id, formalism='classical')
            if stored_plan:
                plan = stored_plan.splitlines()
            # if there is no stored plan to use, ask the planner to solve the current problem
            else:
                data = {"domain": str(self.domain), "problem": str(self.problem)}
                if self.pddl_dom and self.pddl_prob:
                    data = {
                        "domain": open(self.pddl_dom, "r").read(),
                        "problem": open(self.pddl_prob, "r").read(),
                    }

                headers = {"persistent": "true"}

                def get_api_response(delays: List[int]):
                    if delays:
                        sleep(delays[0])
                        try:
                            service_url = "https://solver.planning.domains:5001/package/lama-first/solve"
                            solve_request = requests.post(service_url, json=data, headers=headers).json()
                            celery_result = requests.get("https://solver.planning.domains:5001/" +
                                                         solve_request['result'])
                            while celery_result.json().get("status", "") == 'PENDING':
                                sleep(delays[0])
                                celery_result = requests.get("https://solver.planning.domains:5001/" +
                                                             solve_request['result'])
                            return celery_result.json()['result']['output']['sas_plan'].splitlines()

                        except KeyError:
                            return get_api_response(delays[1:])

                plan = get_api_response([0, 1, 3, 5, 10])
                if plan is None:
                    raise PlanningDomainsAPIError(
                        "Could not get a valid response from the planning.domains solver after 5 attempts.",
                    )

        else:
            with open(filename, "r") as f:
                plan = f.read().splitlines()

        # skip blank lines and comments, such as the plan's cost
        steps = [s.strip() for s in plan if s.strip() and not s.strip().startswith(";")]
        return Plan([self._plan_step_to_action(step) for step in steps])

    def generate_single_trace_from_plan(self, plan: Plan):
        """Generates a single trace from the plan taken as input.

        Args:
            plan (Plan):
                The plan to generate a trace from.

        Returns:
            The trace generated from the plan.
        """
        trace = Trace()
        actions = plan.actions
        plan_len = len(actions)
        # get initial state
        state = self.task.initial_state
        # note that we add 1 because the states represented take place BEFORE their subsequent action,
        # so if we need to take x actions, we need x + 1 states and therefore x + 1 steps in the trace.
        for i in range(plan_len + 1):
            macq_state = self.state_to_macq(state)
            # if we have not yet reached the end of the trace
            if len(trace) < plan_len:
                act = actions[i]
                trace.append(Step(macq_state, self.action_to_macq(act), i + 1))
                state = self.task.progress(state, act)
            else:
                trace.append(Step(macq_state, None, i + 1))
        return trace


def _split_effects(action: GroundAction) -> Tuple[List[Predicate], List[Predicate]]:
    """Splits an action's effects into the atoms it adds and the atoms it deletes."""
    literals = get_strips_literal_list(action.effect)
    adds = [literal for literal in literals if isinstance(literal, Predicate)]
    deletes = [
        literal.argument for literal in literals if not isinstance(literal, Predicate)
    ]
    return adds, deletes


def _type_name(term) -> str:
    """Names a parameter's type, which is `object` if none was declared."""
    return next(iter(sorted(term.type_tags)), "object")


def _match_name(word: str, names: Iterable[str]) -> str:
    """Finds the name a word refers to, preferring an exact match over a case-insensitive one."""
    names = list(names)
    if word in names:
        return word
    matches = [name for name in names if name.lower() == word.lower()]
    if len(matches) != 1:
        raise KeyError(word)
    return matches[0]
