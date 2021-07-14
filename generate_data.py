
from macq.generate.pddl import VanillaSampling
import json

toforbid = ['do-saw-small', 'do-saw-medium', 'do-saw-large', 'load-highspeed-saw']

PLAN_ID = 2478
NUM_TRACES = 32
LENGTH = 20

TRACES = {}
VOCAB = {}

for fb in toforbid:

    print("Building traces to forbid %s actions..." % fb)

    traces = VanillaSampling(problem_id = PLAN_ID, plan_len = LENGTH, num_traces = NUM_TRACES, forbid=fb).traces

    if VOCAB == {}:
        VOCAB = sorted([str(f) for f in traces[0].fluents])

    TRACES[fb] = []
    for t in traces:
        trace = []
        for step in t.steps:
            trace.append([])
            for f in step.state.fluents:
                if step.state.fluents[f]:
                    trace[-1].append(str(f))
        TRACES[fb].append(trace)


DATA = {'vocab': VOCAB, 'traces': TRACES}

# Write the DATA to a file in JSON format
with open('plan_data.json', 'w') as f:
    json.dump(DATA, f)

print("Done!")
