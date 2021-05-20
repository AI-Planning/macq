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

def generate_traces(dom, prob, plan_len : int, num_traces : int):
    """
	Generates traces randomly by uniformly sampling applicable actions to find plans
	of the given length.

	Arguments
	---------
	dom : file
		The domain file.
	prob : file
		The problem file.
	plan_len : int
		The length of each generated trace.
	num_traces : int
		The number of traces to generate.

	Returns
	-------
	traces : TraceList
		The list of traces generated.
    """

    reader = PDDLReader(raise_on_error=True)
    reader.parse_domain(dom)
    problem = reader.parse_instance(prob)
    writer = FstripsWriter(problem)
    # print(problem.actions)
    # print(writer.get_predicates())
    _extract_action_typing(problem)
    _extract_predicate_typing(writer)
    lang = problem.language
    grounder = tarski.grounding.LPGroundingStrategy(reader.problem)
    actions = grounder.ground_actions()
    operators = ground_problem_schemas_into_plain_operators(problem)
    instance = GroundForwardSearchModel(problem, operators)

    traces = TraceList()
    for i in range(num_traces):
        trace = Trace()
        state = problem.init
        for j in range(plan_len):
            app_act = instance.applicable(state)
            ls = []
            for item in app_act:
                ls.append(item)
            act = random.choice(ls)
            
            action = tarski_act_to_macq(act, problem)
            #trace.append(Step(Action(act), State(state)))
            #next_state = progress(state, act)
        traces.append(trace)

def _extract_action_typing(problem: tarski.fstrips.problem.Problem):
    actions = problem.actions
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

def _extract_predicate_typing(writer: FstripsWriter):
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

def tarski_act_to_macq(act: tarski.fstrips.action.PlainOperator, problem: tarski.fstrips.problem.Problem):
    print(act)
    action_info = typing_split(act.name, problem, True)
    precond = []
    raw_precond = act.precondition.subformulas
    for fluent in raw_precond:
        precond.append(tarski_fluent_to_macq(str(fluent), problem))
    print(raw_precond)
    print(act.effects)
    (add, delete) = effect_split(act, problem)
    action = Action(action_info['name'], action_info['objects'], precond, add, delete)
    print(action)
    return action

def tarski_fluent_to_macq(raw: str, problem: tarski.fstrips.problem.Problem):
    #fluents = fluents.subformulas
    # remove starting and ending parentheses, if necessary
    if raw[0] == '(':
        raw = raw[1:len(raw) - 1]
    test =  raw.split(' ')
    if 'not' in test:
        value = False
    else:
        value = True
    fluent = typing_split(test[-1], problem, False)
    macq_fluent = Fluent(fluent['name'], fluent['objects'], value)
    return macq_fluent

def effect_split(act: tarski.fstrips.action.PlainOperator, problem: tarski.fstrips.problem.Problem):
    effects = act.effects
    add = []
    delete = []
    for i in range(len(effects)):
        eff_str = effects[i].tostring()
        fluent = tarski_fluent_to_macq(eff_str[3:], problem)
        if eff_str[:3] == 'ADD':
            add.append(fluent)
        else:
            delete.append(fluent)
    return(add, delete)

def typing_split(raw: str, problem: tarski.fstrips.problem.Problem, is_action: bool):
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
            act_types = _extract_action_typing(problem)
            types = act_types[name]
        else:
            fluent_types = _extract_predicate_typing(FstripsWriter(problem))
            types = fluent_types[name]

    for i in range(num_param):
        obj_param.append(CustomObject(types[i], param_names[i]))
    split['name'] = name
    split['objects'] = obj_param
    return split

def tarski_state_to_macq(state: tarski.model.Model):
    for fluent in state:
        print(fluent)

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests 
    base = Path(__file__).parent.parent.parent
    dom = (base / 'tests/pddl_testing_files/domain.pddl').resolve()
    prob = (base / 'tests/pddl_testing_files/problem.pddl').resolve()
    generate_traces(dom, prob, 1, 1)