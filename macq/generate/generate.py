#from ..trace import TraceList, Trace
from macq.trace import TraceList, Trace
import tarski
from tarski.io import PDDLReader
from pathlib import Path

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
    actions = problem.actions
    lang = problem.language
    precond = {}
    for get_act in actions:
        action = problem.get_action(get_act)
        precond[action.name] = action.precondition

    state = problem.init
    action1 = list(problem.actions)[0]
    song = lang.get('classical_song')
    test = precond[action1]
    print(type(problem.goal))
    print(type(test))
    print(state[problem.goal])
    print(state)
    print()
    print(problem.goal)
    print(test)
    #doesn't work because you need a predicate formula with "concrete" atoms
    print(state[test])

    traces = TraceList()
    for i in range(num_traces):
        trace = Trace()
        # get initial state
        state = problem.init
        
        
        for j in range(plan_len):
            app_act = []
            # get applicable actions
            # get all actions and preconditions; compare to the current state
            for action in list(problem.actions):
                if problem.init[precond[action]]:
                    app_act.append(action)
                print(app_act)
                

            

# exit out to the base macq folder so we can get to /tests 
base = Path(__file__).parent.parent.parent
dom = (base / 'tests/pddl_testing_files/domain.pddl').resolve()
prob = (base / 'tests/pddl_testing_files/problem.pddl').resolve()
generate_traces(dom, prob, 1, 1)

