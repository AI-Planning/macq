# from ..trace import TraceList, Trace
import random
from macq.trace import TraceList, Trace, Step, Action, State, CustomObject, Fluent
from pathlib import Path
import tarski
from tarski.io import PDDLReader, FstripsWriter
from tarski.search import GroundForwardSearchModel
from tarski.search.operations import progress, is_applicable
from tarski.grounding import LPGroundingStrategy
from tarski.grounding.lp_grounding import ground_problem_schemas_into_plain_operators
from tarski.grounding.errors import ReachabilityLPUnsolvable
from tarski.syntax.ops import CompoundFormula, flatten
from tarski.syntax.formulas import Atom
from tarski.syntax.builtins import BuiltinPredicateSymbol
from tarski.utils.helpers import parse_atom
from tarski.fstrips.fstrips import AddEffect, DelEffect
from collections import OrderedDict

import requests
from macq.generate.pddl.planning_domains_api import get_problem


class Generate:
    def __init__(self, dom: str = "", prob: str = "", problem_id: int = None):
        # dom = requests.get(get_problem(problem_id)['domain_url']).text
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)

        if problem_id == None:
            reader.parse_domain(dom)
            self.problem = reader.parse_instance(prob)

        else:
            # TODO: Get problem ID extraction working
            dom = requests.get(get_problem(problem_id)["domain_url"]).text
            prob = requests.get(get_problem(problem_id)["problem_url"]).text
            reader.parse_domain_string(dom)
            self.problem = reader.parse_instance_string(prob)
        self.lang = self.problem.language
        # ground the problem
        operators = ground_problem_schemas_into_plain_operators(self.problem)
        self.instance = GroundForwardSearchModel(self.problem, operators)

        # explore, try to get function stuff (see Function class)
        # print(self.lang.functions)

        """
        Class that handles creating a basic PDDL state trace generator. Handles all 
        parsing and stores the problem, language, and grounded instance for the child
        generators to easily access and use. Takes either the raw filenames of the 
        domain and problem, or a problem ID.

        Arguments
        ---------
        dom : str
            The domain filename.
        prob : str
            The problem filename.
        problem_id : int
            The ID of the problem to access.
        """

    def __extract_action_typing(self):
        """
        Retrieves a dictionary mapping all of this problem's actions and the types
        of objects they act upon.

        i.e. given the standard blocks problem/domain, this function would return:
        {'pick-up': ['object'], 'put-down': ['object'], 'stack': ['object', 'object'], 'unstack': ['object', 'object']}

        Returns
        -------
        extracted_act_types : dict
            The dictionary that indicates the types of all the objects each action in
            the problem acts upon.
        """
        extracted_act_types = {}
        actions = self.problem.actions.values()
        for act in actions:
            types = [type.sort.name for type in act.parameters.variables.values()]
            extracted_act_types[act.name] = types
        return extracted_act_types

    def __extract_predicate_typing(self):
        """
        Retrieves a dictionary mapping all of this problem's predicates and the types
        of objects they act upon.

        i.e. given the standard blocks problem/domain, this function would return:
        {'=': ['object', 'object'], '!=': ['object', 'object'], 'on': ['object', 'object'],
        'ontable': ['object'], 'clear': ['object'], 'handempty': [], 'holding': ['object']}

        Returns
        -------
        extracted_pred_types : dict
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

    def _effect_split(self, act: tarski.fstrips.action.PlainOperator):
        effects = act.effects
        add = []
        delete = []
        from tarski.utils.helpers import parse_atom
        from tarski.syntax.formulas import Formula

        for i in range(len(effects)):
            eff_str = effects[i].tostring()[4:-1]
            # attempt to convert to tarski Atom to standardize the tarski_fluent_to_macq function
            """
            if '()' in eff_str:
                atom = Formula()
            else:
                atom = parse_atom(self.lang, eff_str)
            """
            fluent = self._tarski_fluent_to_macq(eff_str)
            if eff_str[:3] == "ADD":
                add.append(fluent)
            else:
                delete.append(fluent)
        return (add, delete)

    def __effect_split(self, act: tarski.fstrips.action.PlainOperator):
        """
        Converts the effects of an action as defined by tarski to fluents as defined by macq.

        Arguments
        ---------
        act : PlainOperator (from tarski.fstrips.action)
            The supplied action, defined using the tarski PlainOperator class.

        Returns
        -------
        (add, delete) : tuple of Fluents
            The lists of add and delete effects, in the form of macq Fluents.
        """
        effects = act.effects
        add = []
        delete = []
        # getting effects from an action!
        # print(type(list(self.problem.actions.values())[0].effects[0].atom))
        for effect in effects:
            fluent = self._tarski_fluent_to_macq(effect.atom)
            if isinstance(effect, AddEffect):
                add.append(fluent)
            else:
                delete.append(fluent)

        return (add, delete)

    def _action_or_predicate_split(self, raw: str, is_action: bool):
        """
        Takes a string representing either an action or fluent in the form of: action/fluent(*objects)
        and parses it to a dictionary that separates the name of the action or fluent from the objects it
        acts upon. The objects are also instantiated with the appropriate type/name.
        Example: pick-up(f) is parsed to {'name': 'pick-up', 'objects': [Type: object, Name: f]}

        Arguments
        ---------
        raw : str
            The raw string containing the action or fluent.
        is_action : bool
            Determines if the string provided is either an action or a fluent.

        Returns
        -------
        split : dict
            The parsed action or fluent, separating its name from its instantiated objects.
        """
        split = {}
        # strip last parentheses
        raw = raw.strip(")")
        # if the string is a regular action or fluent (not a function), this will retrieve its name
        # (i.e. from clear(pos-03-05, get 'clear')
        name = raw.split("(")[0]
        # if it fails, we know the name is on the other side of the parameter (i.e. from (number get
        # 'number')
        if name == "":
            name = raw.split("(")[1]
        raw = raw.replace(" ", "")
        param_names = raw.split("(")[1].split(",")
        num_param = len(param_names)

        # handle case where the action or fluent has no parameters
        if len(param_names) == 1 and param_names[0] == "":
            num_param = 0
        obj_param = []

        if name == "=":
            types = ["object", "object"]
            name = "equal"

        else:
            if is_action:
                act_types = self.__extract_action_typing()
                types = act_types[name]
            else:
                fluent_types = self.__extract_predicate_typing()
                types = fluent_types[name]

        for i in range(num_param):
            obj_param.append(CustomObject(types[i], param_names[i]))
        split["name"] = name
        split["objects"] = obj_param
        return split

    def _tarski_fluent_to_macq(self, atom: Atom):
        """
        Takes a string representing either a fluent in the form of: fluent(*objects)
        and parses it to a dictionary that separates the name of the fluent from the objects it
        acts upon. The objects are also instantiated with the appropriate type/name.
        If the fluent has a 'not' operator, the value of the Fluent is set to False.
        Example: (not on-table(b)) is parsed to a Fluent with name 'on-table', object 'b', and
        is set to False.

        Arguments
        ---------
        raw : str
            The raw string containing the fluent.

        Returns
        -------
        macq_fluent : Fluent
            The generated fluent.
        """

        """
        # remove starting and ending parentheses, if necessary
        if raw[0] == "(":
            raw = raw[1:-1]
        test = raw.split(" ")
        fluent = self._action_or_predicate_split(test[-1], False)
        """
        fluent_name = atom.predicate.name
        terms = atom.subterms
        objects = []
        for term in terms:
            if isinstance(fluent_name, BuiltinPredicateSymbol):
                fluent_name = fluent_name.value
            objects.append(CustomObject(term.sort.name, term.name))
        fluent = Fluent(fluent_name, objects)
        return fluent

    def _tarski_state_to_macq(self, tarski_state: tarski.model.Model):
        """
        Converts a state as defined by tarski to a state as defined by macq.

        Arguments
        ---------
        tarski_state : Model (from tarski.model)
            The supplied state, defined using the tarski Model class.

        Returns
        -------
        macq_state : State
            A state, defined using the macq State class.
        """
        return State([self._tarski_fluent_to_macq(f) for f in tarski_state.as_atoms()])

    def _tarski_act_to_macq(self, tarski_act: tarski.fstrips.action.PlainOperator):
        """
        Converts an action as defined by tarski to an action as defined by macq.

        Arguments
        ---------
        tarski_act : PlainOperator (from tarski.fstrips.action)
            The supplied action, defined using the tarski PlainOperator class.

        Returns
        -------
        macq_act : Action
            An action, defined using the macq Action class.
        """

        precond = []
        raw_precond = tarski_act.precondition.subformulas
        for raw_p in raw_precond:
            if isinstance(raw_p, CompoundFormula):
                precond.append(self._tarski_fluent_to_macq(raw_p.subformulas[0]))
            else:
                precond.append(self._tarski_fluent_to_macq(raw_p))

        action_info = self._action_or_predicate_split(tarski_act.name, True)
        (add, delete) = self.__effect_split(tarski_act)
        name = tarski_act.name.split("(")[0]
        objs = set()
        objs.update(set(fluent.objects) for fluent in add)
        objs.update([fluent.objects for fluent in delete])
        objs.update([fluent.objects for fluent in precond])
        return Action(name, objs, precond, add, delete)
