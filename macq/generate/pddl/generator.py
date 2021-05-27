#from ..trace import TraceList, Trace
import random
from macq.trace import TraceList, Trace, Step, Action, State, CustomObject, Fluent
from pathlib import Path
import tarski
from tarski.io import PDDLReader, FstripsWriter
from tarski.search import GroundForwardSearchModel
from tarski.search.operations import progress, is_applicable
from tarski.grounding.lp_grounding import ground_problem_schemas_into_plain_operators
from tarski.syntax.ops import CompoundFormula
from collections import OrderedDict
import time
from multiprocessing.pool import ThreadPool

MAX_TIME = 30.0

def _trace_timer(generator):
    """
    Checks that a trace is generated within the time indicated by the MAX_TIME
    constant.

    Arguments
    ---------
    generator : function reference
        The generator function to be wrapped with this time-checker.
    """
    def wrapper(*args, **kwargs):
        pool = ThreadPool(processes=1)
        # start the timer
        begin = time.perf_counter()
        current = begin
        thr = pool.apply_async(generator, args=args, kwds=kwargs)
        # continue counting time while the function has not completed
        while not thr.ready(): 
            current = time.perf_counter()
            # raise exception if the function takes too long
            if current - begin > MAX_TIME:
                raise TraceSearchTimeOut()
        # return a successful trace
        return thr.get()
    return wrapper

class TraceSearchTimeOut(Exception):
        """
        Raised when the time it takes to generate (or attempt to generate) a single trace is 
        longer than the MAX_TIME constant. MAX_TIME is 30 seconds by default.
        """

        def __init__(
            self,
            message="The generator function took longer than MAX_TIME in its attempt to generate a trace."
        ):
            super().__init__(message)

class Generator:
    def __init__(self, dom : str, prob : str):
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(dom)
        self.problem = reader.parse_instance(prob)
        self.lang = self.problem.language
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

        Returns
        -------
        extracted_act_types : dict
            The dictionary that indicates the types of all the objects each action in
            the problem acts upon.
        """
        actions = self.problem.actions
        extracted_act_types = {}
        for act in actions:
            raw_types = str(actions[act])
            raw_types = raw_types[len(act) + 1: -1]
            raw_types = raw_types.split(',')
            params = []
            for raw_act in raw_types:
                params.append(raw_act.split(' ')[1])
            extracted_act_types[act] = params
        return extracted_act_types

    def _extract_predicate_typing(self):
        """
        Retrieves a dictionary mapping all of this problem's predicates and the types
        of objects they act upon.

        Returns
        -------
        extracted_pred_types : dict
            The dictionary that indicates the types of all the objects each predicate in
            the problem acts upon.
        """
        writer = FstripsWriter(self.problem)
        extracted_pred_types = {}
        raw_pred = writer.get_predicates().split('\n')
        for i in range(len(raw_pred)):
            raw_pred[i] = raw_pred[i].lstrip()[1:-1]
            raw_pred[i] = raw_pred[i].split(' ')
            name = raw_pred[i][0]
            params = []
            for j in range(1, len(raw_pred[i])):
                check_hyph = '-'in raw_pred[i][j]
                if '-' not in raw_pred[i][j] and '?' not in raw_pred[i][j]:
                    params.append(raw_pred[i][j])
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
        for i in range(len(effects)):
            eff_str = effects[i].tostring()
            fluent = self._tarski_fluent_to_macq(eff_str[3:])
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
            raw = raw[1:len(raw) - 1]
        test =  raw.split(' ')
        if 'not' in test:
            value = False
        else:
            value = True
        fluent = self._action_or_predicate_split(test[-1], False)
        macq_fluent = Fluent(fluent['name'], fluent['objects'], value)
        return macq_fluent

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
        tarski_state = tarski_state.as_atoms()
        fluents = []
        for fluent in tarski_state:
            fluents.append(self._tarski_fluent_to_macq(str(fluent)))
        macq_state = State(fluents)
        return macq_state

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
                precond.append(self._tarski_fluent_to_macq(str(fluent)))
        else:
            raw_precond = tarski_act.precondition
            precond.append(self._tarski_fluent_to_macq(str(raw_precond)))
        
        (add, delete) = self._effect_split(tarski_act)
        macq_act = Action(action_info['name'], action_info['objects'], precond, add, delete)
        return macq_act

    