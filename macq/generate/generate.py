import tarski

def generate_traces(self, dom, prob, plan_len : int, num_traces : int):
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
    grounded_inst = tarski.parse(dom, prob)