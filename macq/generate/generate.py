#from ..trace import TraceList, Trace
import random
from macq.trace import TraceList, Trace, Step, Action, State, CustomObject
from pathlib import Path
import tarski
from tarski.io import PDDLReader
from tarski.search import GroundForwardSearchModel
from tarski.search.operations import progress, is_applicable
from tarski.grounding import LPGroundingStrategy
from tarski.grounding.lp_grounding import ground_problem_schemas_into_plain_operators
from tarski.grounding.errors import ReachabilityLPUnsolvable
from tarski.syntax.ops import CompoundFormula

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
            action = tarski_typed_act_to_macq(act)
            #trace.append(Step(Action(act), State(state)))
            #next_state = progress(state, act)
        traces.append(trace)

def tarski_typed_act_to_macq(act: tarski.fstrips.action.PlainOperator):
    print(act)
    split = typing_split(act.name)

    pre = act.precondition
    print(split)
    print(pre)
    print(split_fluents(pre))

def typing_split(name: str):
    split = {}
    name = name.strip(')')
    takes_param = name.split('(')[0]
    param_names = name.split('(')[1].split(', ')
    num_param = len(param_names)
    obj_param = []
    for i in range(num_param//2):
        obj_param.append(CustomObject(param_names[i + num_param//2], param_names[i]))
    split['takes param'] = takes_param
    split['objects'] = obj_param
    return split

def split_fluents(fluents: CompoundFormula):
    fluents = fluents.subformulas
    for fluent in fluents:
        # remove starting and ending parentheses, if necessary
        name = str(fluent)
        if name[0] == '(':
            name = name.strip(')')
            name = name[1:]
        test =  name.split(' ')
        print(fluent)
        print(name)
        print(test)
        print()
    return fluents

def tarski_state_to_macq(state: tarski.model.Model):
    pass
if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests 
    base = Path(__file__).parent.parent.parent
    dom = (base / 'tests/pddl_testing_files/domain.pddl').resolve()
    prob = (base / 'tests/pddl_testing_files/problem.pddl').resolve()
    generate_traces(dom, prob, 1, 1)