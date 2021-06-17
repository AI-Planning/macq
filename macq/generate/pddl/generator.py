from ...trace import Action, State, PlanningObject, Fluent
from .planning_domains_api import get_problem
from tarski.io import PDDLReader
from tarski.search import GroundForwardSearchModel
from tarski.grounding.lp_grounding import (
    ground_problem_schemas_into_plain_operators,
    LPGroundingStrategy,
)
from tarski.syntax.ops import CompoundFormula
from tarski.syntax.formulas import Atom
from tarski.syntax.builtins import BuiltinPredicateSymbol
from tarski.fstrips.fstrips import AddEffect
from tarski.fstrips.action import PlainOperator
from tarski.model import Model
import requests


class Generator:
    """A Generator.

    A basic PDDL state trace generator. Handles all parsing and stores the problem,
    language, and grounded instance for the child generators to easily access and use.

    Attributes:
        problem (tarski.fstrips.problem.Problem):
            The problem definition.
        lang (tarski.fol.FirstOrderLanguage):
            The language definition.
        instance (tarski.search.model.GroundForwardSearchModel):
            The grounded instance of the problem.
        grounded_fluents (list):
            A list of all grounded (macq) fluents extracted from the given problem definition.
    """

    def __init__(self, dom: str = "", prob: str = "", problem_id: int = None):
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
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        if problem_id == None:
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

    def __get_all_grounded_fluents(self):
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
        for f in tarski_state.as_atoms():
            fluent = self.__tarski_atom_to_macq_fluent(f)
            # ignore functions for now
            if fluent:
                state_fluents[fluent] = True
        for grounded_fluent in self.grounded_fluents:
            if grounded_fluent not in state_fluents.keys():
                state_fluents[grounded_fluent] = False
        return State(state_fluents)

    def tarski_act_to_macq(self, tarski_act: PlainOperator, fully_observable: bool = True):
        """Converts an action as defined by tarski to an action as defined by macq.

        Args:
            tarski_act (PlainOperator):
                The supplied action, defined using the tarski PlainOperator class.
            fully_observable (bool):
                Determines if the generator wants to extract preconditions and effects as well.

        Returns:
            An action, defined using the macq Action class.
        """
        name = tarski_act.name.split("(")[0]
        objs = set()
        if fully_observable:
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
                precond.append(
                    self.__tarski_atom_to_macq_fluent(tarski_act.precondition)
                )
            (add, delete) = self.__effect_split(tarski_act)
            for fluent in add:
                objs.update(set(fluent.objects))
            for fluent in delete:
                objs.update(set(fluent.objects))
            for fluent in precond:
                objs.update(set(fluent.objects))
        return Action(name, objs)
