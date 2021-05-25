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
from collections import OrderedDict

class Generate:
    def __init__(self, dom : str, prob : str):
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        reader.parse_domain(dom)
        self.problem = reader.parse_instance(prob)
        # ground the problem
        operators = ground_problem_schemas_into_plain_operators(self.problem)
        self.instance = GroundForwardSearchModel(self.problem, operators)

    def _extract_action_typing(self):
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

    def _typing_split(self, raw: str, is_action: bool):
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
            # remove starting and ending parentheses, if necessary
            if raw[0] == '(':
                raw = raw[1:len(raw) - 1]
            test =  raw.split(' ')
            if 'not' in test:
                value = False
            else:
                value = True
            fluent = self._typing_split(test[-1], False)
            macq_fluent = Fluent(fluent['name'], fluent['objects'], value)
            return macq_fluent

    def _tarski_state_to_macq(self, state: tarski.model.Model):
        state = state.as_atoms()
        fluents = []
        for fluent in state:
            fluents.append(self._tarski_fluent_to_macq(str(fluent)))
        return State(fluents)

    def _tarski_act_to_macq(self, act: tarski.fstrips.action.PlainOperator):
        action_info = self._typing_split(act.name, True)
        precond = []
        if type(act.precondition) == CompoundFormula:
            raw_precond = act.precondition.subformulas
            for fluent in raw_precond:
                precond.append(self._tarski_fluent_to_macq(str(fluent)))
        else:
            raw_precond = act.precondition
            precond.append(self._tarski_fluent_to_macq(str(raw_precond)))
        
        (add, delete) = self._effect_split(act)
        action = Action(action_info['name'], action_info['objects'], precond, add, delete)
        return action

    