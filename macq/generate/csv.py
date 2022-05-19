# from ..trace import (
from macq.trace import (
    Action,
    Fluent,
    State,
    Step,
    Trace,
    TraceList,
)


def load(fname: str, act_col: str, plan_id_col: str = None):
    """Loads a trace file as a csv into a `TraceList`.

    Args:
        fname (str):
            The name of the trace file to load.
        act_col (str):
            The name of the column in the trace file that contains the action names.
        plan_id_col (str, optional):
            The name of the column in the trace file that contains the plan ID.
            Defaults to None.

    Returns:
        `TraceList`:
            The loaded trace list.
    """
    with open(fname, "r") as f:
        lines = [l.strip().split(",") for l in f.readlines()]

    # Make sure we have at least one plan specified
    if plan_id_col is None:
        plan_id_col = "plan_id"
        lines[0].append(plan_id_col)
        for i in range(1, len(lines)):
            lines[i].append(0)

    assert act_col in lines[0], f"'{act_col}' not in header"
    assert plan_id_col in lines[0], f"'{plan_id_col}' not in header"

    # Turn the csv into a list of dictionaries with the header row as keys
    data = [dict(zip(lines[0], line)) for line in lines[1:]]

    # Assert all data outside of the action column is 0 or 1
    for line in data:
        for key in line:
            if key not in [plan_id_col, act_col]:
                assert line[key] in ["0", "1"], "Fluent columns should be 0 or 1"

    # Separate the data based on the plan ID
    plans = {}

    for line in data:
        if line[plan_id_col] not in plans:
            plans[line[plan_id_col]] = []
        plans[line[plan_id_col]].append(line)

    # Turn the plan data into a list of traces
    traces = TraceList()
    for plan_id in plans:
        trace = Trace()
        for i, bitvec in enumerate(plans[plan_id]):
            state = State(
                {
                    Fluent(f, []): bitvec[f] == "1"
                    for f in bitvec
                    if f not in [act_col, plan_id_col]
                }
            )
            act = Action(bitvec[act_col], [])
            step = Step(state, act, i)
            trace.append(step)
        traces.append(trace)
    return traces
