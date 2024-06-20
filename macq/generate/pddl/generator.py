import re
from time import sleep
from typing import Set, List, Union
from tarski.grounding.common import StateVariableLite
from tarski.io import PDDLReader
from tarski.search import GroundForwardSearchModel
from tarski.search.operations import progress
from tarski.grounding.lp_grounding import (
    ground_problem_schemas_into_plain_operators,
    LPGroundingStrategy,
)
from tarski.syntax import land
from tarski.syntax.ops import CompoundFormula, flatten
from tarski.syntax.formulas import Atom, neg
from tarski.syntax.builtins import BuiltinPredicateSymbol
from tarski.fstrips.action import PlainOperator
from tarski.fstrips.fstrips import AddEffect
from tarski.model import Model, create
from tarski.io import fstrips as iofs

import requests
from tarski.util import SymbolIndex

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


class Generator:
    """A Generator.

    A basic PDDL state trace generator. Handles all parsing and stores the problem,
    language, and grounded instance for the child generators to easily access and use.

    Attributes:
        pddl_dom (str):
            The name of the local PDDL domain filename (relevant if the problem ID is not provided.)
        pddl_prob (str):
            The name of the local PDDL problem filename (relevant if the problem ID is not provided.)
        problem_id (int):
            The ID of the problem to be accessed (relevant if local files are not provided.)
        problem (tarski.fstrips.problem.Problem):
            The problem definition.
        lang (tarski.fol.FirstOrderLanguage):
            The language definition.
        instance (GroundForwardSearchModel):
            The grounded instance of the problem.
        grounded_fluents (list):
            A list of all grounded (macq) fluents extracted from the given problem definition.
        op_dict (dict):
            The problem's ground operators, formatted to a dictionary for easy access during plan generation.
        observe_pres_effs (bool):
            Option to observe action preconditions and effects upon generation.
    """

    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        observe_pres_effs: bool = False,
        observe_static_fluents: bool = False
    ):
        """Creates a basic PDDL state trace generator. Takes either the raw filenames
        of the domain and problem, or a problem ID.

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
        # get attributes
        self.observe_static_fluents = observe_static_fluents
        self.pddl_dom = dom
        self.pddl_prob = prob
        self.problem_id = problem_id
        self.observe_pres_effs = observe_pres_effs
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        if not problem_id:
            reader.parse_domain(dom)
            self.problem = reader.parse_instance(prob)
        else:
            dom = requests.get(get_problem(problem_id, formalism='classical')["domain_url"]).text
            prob = requests.get(get_problem(problem_id, formalism='classical')["problem_url"]).text
            reader.parse_domain_string(dom)
            self.problem = reader.parse_instance_string(prob)
        self.lang = self.problem.language
        # ground the problem
        operators = ground_problem_schemas_into_plain_operators(self.problem)
        self.instance = GroundForwardSearchModel(self.problem, operators)
        self.grounded_fluents = self.__get_all_grounded_fluents()
        self.op_dict = self.__get_op_dict()

    def extract_action_typing(self):
        """Retrieves a dictionary mapping all of this problem's actions and the types
        of objects they act upon.

        i.e. given the standard blocks problem/domain, this function would return:
        {'pick-up': ['object'], 'put-down': ['object'], 'stack': ['object', 'object'],
        'unstack': ['object', 'object']}

        Returns:
            The dictionary that indicates the types of all the objects each action in
            the problem acts upon.
        """
        extracted_act_types = {}
        actions = self.problem.actions.values()
        for act in actions:
            types = [type.sort.name for type in act.parameters.variables.values()]
            extracted_act_types[act.name] = types
        return extracted_act_types

    def extract_predicate_typing(self):
        """Retrieves a dictionary mapping all of this problem's predicates and the types
        of objects they act upon.

        i.e. given the standard blocks problem/domain, this function would return:
        {'=': ['object', 'object'], '!=': ['object', 'object'], 'on': ['object', 'object'],
        'ontable': ['object'], 'clear': ['object'], 'handempty': [], 'holding': ['object']}

        Returns:
            The dictionary that indicates the types of all the objects each predicate in
            the problem acts upon.
        """
        predicates = self.lang.predicates
        extracted_pred_types = {}
        for pred in predicates:
            info = pred.signature
            name = info[0]
            if isinstance(name, BuiltinPredicateSymbol):
                name = name.value
            extracted_pred_types[name] = [type for type in info[1:]]
        return extracted_pred_types

    def __get_op_dict(self):
        """Converts this problem's ground operators into a dictionary format so that the appropriate
        tarski PlainOperators can be referenced when a plan is generated (see `generate_plan`).

        Returns:
            The problem's ground operators, in a formatted dictionary.
        """
        op_dict = {}
        for o in self.instance.operators:
            # special case for actions that don't take parameters
            if "()" in o.name:
                op_dict["".join(["(", o.name[:-2], ")"])] = o
            else:
                # reformat so that operators can be referenced by the same string format the planner uses for actions
                op_dict["".join(["(", o.name.replace("(", " ").replace(",", "")])] = o
        return op_dict

    def __get_all_grounded_fluents(self):
        """Extracts all the grounded fluents in the problem.

        Returns:
            A list of all the grounded fluents in the problem, in the form of macq Fluents.
        """
        l1: list = []
        if not self.observe_static_fluents:
            [self.__tarski_atom_to_macq_fluent(grounded_fluent.to_atom())for grounded_fluent in LPGroundingStrategy(
                self.problem, include_variable_inequalities=True).ground_state_variables().objects]
        if self.observe_static_fluents:
            l1 = [
                self.__tarski_atom_to_macq_fluent(grounded_fluent.to_atom())
                for grounded_fluent in ExtractStaticFluents(
                    self.problem, include_variable_inequalities=True).ground_state_variables().objects]
        return l1

    def __effect_split(self, act: PlainOperator):
        """Converts the effects of an action as defined by tarski to fluents as defined by macq.

        Args:
            act (PlainOperator from tarski.fstrips.action):
                The supplied action, defined using the tarski PlainOperator class.

        Returns:
            The lists of add and delete effects, in the form of a tuple macq Fluents (add, delete).
        """
        effects = act.effects
        add = set()
        delete = set()
        for effect in effects:
            fluent = self.__tarski_atom_to_macq_fluent(effect.atom)
            if isinstance(effect, AddEffect):
                add.add(fluent)
            else:
                delete.add(fluent)
        return (add, delete)

    def __tarski_atom_to_macq_fluent(self, atom: Atom):
        """Converts a tarski Atom to a fluent as defined by macq.

        Args:
            atom (Atom):
                The supplied atom, defined using the tarski Atom class.

        Returns:
            A fluent, defined using the macq Fluent class.
        """
        # ignore functions for now
        if not isinstance(atom, Atom):
            return None
        fluent_name = atom.predicate.name
        terms = atom.subterms
        objects = []
        for term in terms:
            if isinstance(fluent_name, BuiltinPredicateSymbol):
                fluent_name = fluent_name.value
            objects.append(PlanningObject(term.sort.name, term.name))
        fluent = Fluent(fluent_name, objects)
        return fluent

    def tarski_state_to_macq(self, tarski_state: Model):
        """Converts a state as defined by tarski to a state as defined by macq.

        Args:
            tarski_state (Model):
                The supplied state, defined using the tarski Model class.

        Returns:
            A state, defined using the macq State class.
        """
        state_fluents = {}
        true_fluents = set()
        for f in tarski_state.as_atoms():
            fluent = self.__tarski_atom_to_macq_fluent(f)
            # ignore functions for now
            if fluent:
                true_fluents.add(str(fluent))
        for grounded_fluent in self.grounded_fluents:
            state_fluents[grounded_fluent] = str(grounded_fluent) in true_fluents

        return State(state_fluents)

    def tarski_act_to_macq(self, tarski_act: PlainOperator):
        """Converts an action as defined by tarski to an action as defined by macq.

        Args:
            tarski_act (PlainOperator):
                The supplied action, defined using the tarski PlainOperator class.

        Returns:
            An action, defined using the macq Action class.
        """
        name_split = tarski_act.name.replace(")", "").split("(")
        name = name_split[0]
        obj_names = name_split[1].split(", ")

        tarski_objs_mapping = {}
        precond = set()
        if isinstance(tarski_act.precondition, CompoundFormula):
            raw_precond = tarski_act.precondition.subformulas
            for raw_p in raw_precond:
                if isinstance(raw_p, CompoundFormula):
                    precond.add(self.__tarski_atom_to_macq_fluent(raw_p.subformulas[0]))
                else:
                    precond.add(self.__tarski_atom_to_macq_fluent(raw_p))
        else:
            precond.add(self.__tarski_atom_to_macq_fluent(tarski_act.precondition))
        (add, delete) = self.__effect_split(tarski_act)

        tarski_objs_mapping.update({o.name:o for fluent in add for o in fluent.objects })
        tarski_objs_mapping.update({o.name:o for fluent in delete for o in fluent.objects })
        tarski_objs_mapping.update({o.name:o for fluent in precond for o in fluent.objects })

        obj_params = [tarski_objs_mapping[o] for o in obj_names]

        return (
            Action(
                name=name,
                obj_params=obj_params,
                precond=precond,
                add=add,
                delete=delete,
            )
            if self.observe_pres_effs
            else Action(name=name, obj_params=obj_params)
        )


    def change_init(
        self,
        init_fluents: Union[Set[Fluent], List[Fluent]],
        new_domain: str = "new_domain.pddl",
        new_prob: str = "new_prob.pddl",
    ):
        """Changes the initial state of the `Generator`. The domain and problem PDDL files
        are rewritten to accomodate the new goal for later use by a planner.

        Parameters:
            init_fluents (Union[Set[Fluent], List[Fluent]]):
                The collection of fluents that will make up the new initial state.
            new_domain (str):
                The name of the new domain file.
            new_prob (str):
                The name of the new problem file.
        """
        init = create(self.lang)
        for f in init_fluents:
            # convert fluents to tarski Atoms
            atom = Atom(
                self.lang.get_predicate(f.name),
                [self.lang.get(o.name) for o in f.objects],
            )
            init.add(atom.predicate, *atom.subterms)
        self.problem.init = init

        # rewrite PDDL files appropriately
        writer = iofs.FstripsWriter(self.problem)
        writer.write(new_domain, new_prob)
        self.pddl_dom = new_domain
        self.pddl_prob = new_prob

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
        available_f = self.grounded_fluents
        for f in goal_fluents:
            if f not in available_f:
                raise InvalidGoalFluent(f)

        # convert the given set of fluents into a formula
        if not goal_fluents:
            goal = land()
        else:
            goal = land(
                *[
                    Atom(
                        self.lang.get(f.name),
                        [self.lang.get_constant(o.name) for o in f.objects],
                    )
                    for f in goal_fluents
                ]
            )
        # reset the goal
        self.problem.goal = flatten(goal)

        # rewrite PDDL files appropriately
        writer = iofs.FstripsWriter(self.problem)
        writer.write(new_domain, new_prob)
        self.pddl_dom = new_domain
        self.pddl_prob = new_prob

    def generate_plan(self, from_ipc_file: bool = False, filename: str = None):
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
        """
        if not from_ipc_file:
            # if the files are only being generated from the problem ID and are unaltered, retrieve the existing plan (note that
            # if any changes were made, the local files would be used as the PDDL files are rewritten when changes are made).
            if self.problem_id and not self.pddl_dom and not self.pddl_prob:
                plan = get_plan(self.problem_id, formalism='classical')
            # if you are not just using the unaltered files, use the local files instead
            else:
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
                            sas_plan = celery_result.json()['result']['output']['sas_plan']
                            actions_with_objects = re.findall(r'\((.*?)\)', sas_plan)

                            plan_list = [f'({action})' for action in actions_with_objects]
                            return plan_list

                        except TypeError:
                            return get_api_response(delays[1:])

                plan = get_api_response([0, 1, 3, 5, 10])
                if plan is None:
                    raise PlanningDomainsAPIError(
                        "Could not get a valid response from the planning.domains solver after 5 attempts.",
                    )

        else:
            f = open(filename, "r")
            plan = list(filter(lambda x: ";" not in x, f.read().splitlines()))

        # convert to a list of tarski PlainOperators (actions)
        return Plan([self.op_dict[p] for p in plan if p in self.op_dict])

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
        state = self.problem.init
        # note that we add 1 because the states represented take place BEFORE their subsequent action,
        # so if we need to take x actions, we need x + 1 states and therefore x + 1 steps in the trace.
        for i in range(plan_len + 1):
            macq_state = self.tarski_state_to_macq(state)
            # if we have not yet reached the end of the trace
            if len(trace) < plan_len:
                act = actions[i]
                trace.append(Step(macq_state, self.tarski_act_to_macq(act), i + 1))
                state = progress(state, act)
            else:
                trace.append(Step(macq_state, None, i + 1))
        return trace


class ExtractStaticFluents(LPGroundingStrategy):
    def __init__(self, problem, ground_actions=True, include_variable_inequalities=False):
        super().__init__(problem=problem, ground_actions=ground_actions,
                         include_variable_inequalities=include_variable_inequalities)

    def ground_state_variables(self):
        """ Create and index all state variables of the problem by exhaustively grounding all predicate and function
        symbols that are considered to be fluent with respect to the problem constants. Thus, if the problem has one
        fluent predicate "p" and one static predicate "q", and constants "a", "b", "c", the result of this operation
        will be the state variables "p(a)", "p(b)" and "p(c)".
        """
        model = self._solve_lp()

        variables = SymbolIndex()
        for symbol in self.fluent_symbols.union(self.static_symbols):

            lang = symbol.language
            key = 'atom_' + symbol.name
            if key in model:  # in case there is no reachable ground state variable from that fluent symbol
                for binding in model[key]:
                    binding_with_constants = tuple(lang.get(c) for c in binding)
                    variables.add(StateVariableLite(symbol, binding_with_constants))

        return variables
