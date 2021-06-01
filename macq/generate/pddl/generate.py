#from ..trace import TraceList, Trace
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
from tarski.utils.helpers import parse_atom
from collections import OrderedDict

class Generate:
    def __init__(self, dom : str, prob : str):
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(dom)
        self.problem = reader.parse_instance(prob)
        self.lang = self.problem.language
        # print(reader.parse_string('(has_genre ?x1 - song ?x2 - genre)', 'single_predicate_definition'))
        # ground the problem
        operators = ground_problem_schemas_into_plain_operators(self.problem)
        self.instance = GroundForwardSearchModel(self.problem, operators)

        """
        Class that handles creating a basic PDDL state trace generator. Handles all 
        parsing and stores the problem, language, and grounded instance for the child
        generators to easily access and use. 

        Arguments
        ---------
        dom : str
            The domain filename.
        prob : str
            The problem filename.
        """

    def _extract_action_typing(self):
        """
        Retrieves a dictionary mapping all of this problem's actions and the types
        of objects they act upon.

        i.e. given the standard blocks problem/domain, this function would return:
        {'pick-up': ['block'], 'put-down': ['block'], 'stack': ['block', 'block'], 'unstack': ['block', 'block']}

        Returns
        -------
        extracted_act_types : dict
            The dictionary that indicates the types of all the objects each action in
            the problem acts upon.
        """
        # retrieve all actions (actions will be an OrderedDict of all actions in the domain)
        actions = self.problem.actions
        extracted_act_types = {}
        for act in actions:
            # retrieves each action; i.e. stack(?x: object,?y: object)
            raw_types = str(actions[act])
            # get the type/object the action is acting on; i.e. ?x: object,?y: object
            raw_types = raw_types[len(act) + 1: -1]
            params = []
            # only need to retrieve type information if this action takes parameters;
            # otherwise the parameters will remain an empty list
            if raw_types != '':
                # split up the objects if they are multiple; i.e. ['?x: object', '?y: object']
                raw_types = raw_types.split(',')
                for raw_act in raw_types:
                    # get the object types; i.e. retrieve ['object', 'object'] as stack takes two 'object' types
                    params.append(raw_act.split(' ')[1])
            # add this action and its typing to the dictionary
            extracted_act_types[act] = params
        return extracted_act_types

    def _extract_predicate_typing(self):
        """
        Retrieves a dictionary mapping all of this problem's predicates and the types
        of objects they act upon.

        i.e. given the standard blocks problem/domain, this function would return:
        {'on': ['block', 'block'], 'ontable': ['block'], 'clear': ['block'], 'handempty': [''], 'holding': ['block']}

        Returns
        -------
        extracted_pred_types : dict
            The dictionary that indicates the types of all the objects each predicate in
            the problem acts upon.
        """
        writer = FstripsWriter(self.problem)
        extracted_pred_types = {}
        # get all predicates and split them up to get them individually (will get something 
        # like (on ?x1 - block ?x2 - block) for each predicate)
        raw_pred = writer.get_predicates().split('\n')
        print(raw_pred)
        # loop through all predicates
        for i in range(len(raw_pred)):
            # remove starting and ending parentheses 
            raw_pred[i] = raw_pred[i].lstrip()[1:-1]
            # split up the components of the predicate
            raw_pred[i] = raw_pred[i].split(' ')
            # the first component will be the name of the predicate, i.e. 'on'
            name = raw_pred[i][0]
            params = []
            # loop through the rest of the components
            for j in range(1, len(raw_pred[i])):
                # if the component isn't a parameter (i.e. ?x1) or isn't a hyphen, then
                # it is a type; add it to the list
                if '-' not in raw_pred[i][j] and '?' not in raw_pred[i][j]:
                    params.append(raw_pred[i][j])
            # this predicate uses this list of types
            extracted_pred_types[name] = params    
        return extracted_pred_types

    def _effect_split(self, act: tarski.fstrips.action.PlainOperator):
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
        from tarski.utils.helpers import parse_atom
        from tarski.syntax.formulas import Formula
        for i in range(len(effects)):
            eff_str = effects[i].tostring()[4:-1]
            print(eff_str)
            # attempt to convert to tarski Atom to standardize the tarski_fluent_to_macq function
            '''
            if '()' in eff_str:
                atom = Formula()
            else:
                atom = parse_atom(self.lang, eff_str)
            '''
            fluent = self._tarski_fluent_to_macq(eff_str)
            if eff_str[:3] == 'ADD':
                add.append(fluent)
            else:
                delete.append(fluent)
        return(add, delete)

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
        raw = raw.strip(')')
        name = raw.split('(')[0]
        raw = raw.replace(' ', '')
        param_names = raw.split('(')[1].split(',')
        num_param = len(param_names)
        # handle case where the action or fluent has no parameters
        if len(param_names) == 1 and param_names[0] == '':
            num_param = 0
        obj_param = [] 

        if name == '=':
            types = ['object', 'object']
            name = 'equal'
        else:
            if is_action:
                act_types = self._extract_action_typing()
                types = act_types[name]
            else:
                fluent_types = self._extract_predicate_typing()
                types = fluent_types[name]

        for i in range(num_param):
            obj_param.append(CustomObject(types[i], param_names[i]))
        split['name'] = name
        split['objects'] = obj_param
        return split

    def _tarski_fluent_to_macq(self, raw: str):
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
        # remove starting and ending parentheses, if necessary
        if raw[0] == '(':
            raw = raw[1:-1]
        test =  raw.split(' ')
        value = 'not' not in test
        fluent = self._action_or_predicate_split(test[-1], False)
        return Fluent(fluent['name'], fluent['objects'], value)

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
        return State([self._tarski_fluent_to_macq(str(f)) for f in tarsi_state.as_atoms()])

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
        action_info = self._action_or_predicate_split(tarski_act.name, True)
        precond = []
        if type(tarski_act.precondition) == CompoundFormula:
            raw_precond = tarski_act.precondition.subformulas
            for fluent in raw_precond:
                #print(type(fluent))
                precond.append(self._tarski_fluent_to_macq(str(fluent)))
        else:
            raw_precond = tarski_act.precondition
            precond.append(self._tarski_fluent_to_macq(str(raw_precond)))
        
        (add, delete) = self._effect_split(tarski_act)
        return Action(action_info['name'], action_info['objects'], precond, add, delete)

    