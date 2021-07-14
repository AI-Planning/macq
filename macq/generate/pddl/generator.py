from ...trace import Action, State, PlanningObject, Fluent
from .planning_domains_api import get_problem, get_plan
from typing import Set
from tarski.io import PDDLReader
from tarski.search import GroundForwardSearchModel
from tarski.grounding.lp_grounding import (
    ground_problem_schemas_into_plain_operators,
    LPGroundingStrategy,
)
from tarski.syntax.ops import CompoundFormula, Variable
from tarski.syntax.formulas import Atom
from tarski.syntax.builtins import BuiltinPredicateSymbol
from tarski.fstrips.fstrips import AddEffect
from tarski.fstrips.action import PlainOperator
from tarski.model import Model
from tarski.syntax import land, Sort
from tarski.io import fstrips as iofs
import requests


class InvalidGoalFluent(Exception):
    """
    Raised when the user attempts to supply a new goal with invalid fluent(s).
    """

    def __init__(
        self,
        message="The fluents provided contain one or more fluents not available in this problem.",
    ):
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
        instance (tarski.search.model.GroundForwardSearchModel):
            The grounded instance of the problem.
        grounded_fluents (list):
            A list of all grounded (macq) fluents extracted from the given problem definition.
        op_dict (dict):
            The problem's ground operators, formatted to a dictionary for easy access during plan generation.
    """

    def __init__(self, dom: str = None, prob: str = None, problem_id: int = None):
        """Creates a basic PDDL state trace generator. Takes either the raw filenames
        of the domain and problem, or a problem ID.

        Args:
            dom (str):
                The domain filename.
            prob (str):
                The problem filename.
            problem_id (int):
                The ID of the problem to access.
        """
        # get attributes
        self.pddl_dom = dom
        self.pddl_prob = prob
        self.problem_id = problem_id
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        if not problem_id:
            reader.parse_domain(dom)
            self.problem = reader.parse_instance(prob)
        else:
            dom = requests.get(get_problem(problem_id)["domain_url"]).text
            prob = requests.get(get_problem(problem_id)["problem_url"]).text
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
            # reformat so that operators can be referenced by the same string format the planner uses for actions
            op_dict["".join(["(", o.name.replace("(", " ").replace(",", "")])] = o
        return op_dict

    def __get_all_grounded_fluents(self):
        """Extracts all the grounded fluents in the problem.

        Returns:
            A list of all the grounded fluents in the problem, in the form of macq Fluents.
        """
        return [
            self.__tarski_atom_to_macq_fluent(grounded_fluent.to_atom())
            for grounded_fluent in LPGroundingStrategy(
                self.problem, include_variable_inequalities=True
            )
            .ground_state_variables()
            .objects
        ]

    def __effect_split(self, act: PlainOperator):
        """Converts the effects of an action as defined by tarski to fluents as defined by macq.

        Args:
            act (PlainOperator from tarski.fstrips.action):
                The supplied action, defined using the tarski PlainOperator class.

        Returns:
            The lists of add and delete effects, in the form of a tuple macq Fluents (add, delete).
        """
        effects = act.effects
        add = []
        delete = []
        for effect in effects:
            fluent = self.__tarski_atom_to_macq_fluent(effect.atom)
            if isinstance(effect, AddEffect):
                add.append(fluent)
            else:
                delete.append(fluent)
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
        name = tarski_act.name.split("(")[0]
        objs = set()
        precond = []
        if isinstance(tarski_act.precondition, CompoundFormula):
            raw_precond = tarski_act.precondition.subformulas
            for raw_p in raw_precond:
                if isinstance(raw_p, CompoundFormula):
                    precond.append(
                        self.__tarski_atom_to_macq_fluent(raw_p.subformulas[0])
                    )
                else:
                    precond.append(self.__tarski_atom_to_macq_fluent(raw_p))
        else:
            precond.append(self.__tarski_atom_to_macq_fluent(tarski_act.precondition))
        (add, delete) = self.__effect_split(tarski_act)
        for fluent in add:
            objs.update(set(fluent.objects))
        for fluent in delete:
            objs.update(set(fluent.objects))
        for fluent in precond:
            objs.update(set(fluent.objects))
        return Action(name, list(objs))

    def change_goal(self, goal_fluents: Set[Fluent], new_domain: str, new_prob: str):
        """Changes the goal of the `Generator`. The domain and problem PDDL files
        are rewritten to accomodate the new goal for later use by a planner.

        Args:
            goal_fluents (Set[Fluent]):
                The set of fluents to make up the new goal.
            new_domain (str):
                The name of the new domain file.
            new_prob (str):
                The name of the new problem file.

        Raises:
            InvalidGoalFluent:
                Raised if any of the fluents supplied do not exist in this domain.
        """
        # check if the fluents to add are valid
        available_f = self.__get_all_grounded_fluents()
        for f in goal_fluents:
            if f not in available_f:
                raise InvalidGoalFluent()

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
        self.problem.goal = goal

        # rewrite PDDL files appropriately
        writer = iofs.FstripsWriter(self.problem)
        writer.write(new_domain, new_prob)
        self.pddl_dom = new_domain
        self.pddl_prob = new_prob

    def generate_plan(self, write_to_file: bool = False, filename: str = None):
        """Generates a plan. If the goal was changed, the new goal is taken into account.
        Otherwise, the default goal in the initial problem file is used.

        Args:
            write_to_file (bool, optional):
                Option to write the plan to a file. Defaults to False.
            filename (str, optional):
                The name of the file to (optionally) write the plan to. Defaults to None.

        Returns:
            A list of tarski PlainOperators representing the actions taken in this plan.
        """
        # if the files are only being generated from the problem ID and are unaltered, retrieve the existing plan (note that
        # if any changes were made, the local files would be used as the PDDL files are rewritten when changes are made).
        if self.problem_id and not self.pddl_dom and not self.pddl_prob:
            plan = get_plan(self.problem_id)
            if write_to_file:
                with open(filename, "w") as f:
                    f.write("\n".join(act for act in plan))
        # if you are not just using the unaltered files, use the local files instead
        else:
            data = {
                "domain": open(self.pddl_dom, "r").read(),
                "problem": open(self.pddl_prob, "r").read(),
            }
            resp = requests.post(
                "http://solver.planning.domains/solve", verify=False, json=data
            ).json()
            plan = [act["name"] for act in resp["result"]["plan"]]
            if write_to_file:
                with open(filename, "w") as f:
                    f.write("\n".join(act for act in plan))
        # convert to a list of tarski PlainOperators (actions)
        return [self.op_dict[p] for p in plan if p in self.op_dict.keys()]
