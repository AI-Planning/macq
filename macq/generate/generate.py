#from ..trace import TraceList, Trace
import random
from macq.trace import TraceList, Trace, Step, Action, State
from pathlib import Path
import tarski
from tarski.io import PDDLReader
from tarski.search import GroundForwardSearchModel
from tarski.search.operations import progress, is_applicable
from tarski.grounding import LPGroundingStrategy
from tarski.grounding.lp_grounding import ground_problem_schemas_into_plain_operators
from tarski.grounding.errors import ReachabilityLPUnsolvable

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
    #actions = [value for value in problem.actions.values()]
    grounder = tarski.grounding.LPGroundingStrategy(reader.problem)
    actions = grounder.ground_actions()
    print(actions)
    print()
    print(grounder.ground_state_variables())
    operators = ground_problem_schemas_into_plain_operators(problem)
    print()
    print(operators)
    instance = GroundForwardSearchModel(problem, operators)

    #is_applicable(problem.init,grounder.ground_state_variables()[0])

    #try again with ground forward - ask why you get errors here and inspect the errors deeper
    #(grounded operator -> action w/ no parameters? but there is no other applicable function...
    # and then just trying to use is_applicable doesn't work....)

    traces = TraceList()
    for i in range(num_traces):
        trace = Trace()
        state = problem.init
        for j in range(plan_len):
            app_act = instance.applicable(state)
            print(app_act)
            ls = []
            for item in app_act:
                #pass
                ls.append(item)
            act = random.choice(ls)
            trace.append(Step(Action(act), State(state)))
            next_state = progress(state, act)
        traces.append(trace)

#def tarski_act_to_macq(act: ):

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests 
    base = Path(__file__).parent.parent.parent
    dom = (base / 'tests/pddl_testing_files/domain.pddl').resolve()
    prob = (base / 'tests/pddl_testing_files/problem.pddl').resolve()
    generate_traces(dom, prob, 1, 1)