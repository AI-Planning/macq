from macq.extract import Extract, modes
from macq.trace import *


def real_trace_list():
    # Objects
    blockA = CustomObject("block", "A")
    blockB = CustomObject("block", "B")

    objects = [blockA, blockB]

    # Fluents
    a_clear = Fluent("A clear", [blockA])
    b_clear = Fluent("B clear", [blockB])
    a_on_table = Fluent("A on table", [blockA])
    b_on_table = Fluent("B on table", [blockB])
    holding_a = Fluent("holding A", [blockA])
    holding_b = Fluent("holding B", [blockB])
    a_on_b = Fluent("A on B", [blockA, blockB])
    b_on_a = Fluent("B on A", [blockA, blockB])

    # Actions
    pick_up = Action("pick up", [blockA, blockB])
    put_down = Action("put down", [blockA, blockB])
    stack = Action("stack", [blockA, blockB])
    unstack = Action("unstack", [blockA, blockB])
    # actions = [pick_up, put_down, stack, unstack]

    # Traces
    t1 = Trace(
        [
            Step(
                State(
                    {
                        a_clear: True,
                        b_clear: True,
                        a_on_table: True,
                        b_on_table: True,
                    }
                ),
                pick_up,
            ),
            Step(
                State(
                    {
                        b_clear: True,
                        a_on_table: False,
                        b_on_table: True,
                        holding_a: True,
                    }
                ),
                stack,
            ),
            Step(
                State(
                    {
                        a_clear: True,
                        b_clear: False,
                        b_on_table: True,
                        a_on_b: True,
                    }
                ),
                None,
            ),
        ]
    )

    t2 = Trace(
        [
            Step(
                State(
                    {
                        a_clear: True,
                        b_clear: True,
                        a_on_table: True,
                        b_on_table: True,
                    }
                ),
                pick_up,
            ),
            Step(
                State(
                    {
                        a_clear: True,
                        a_on_table: True,
                        b_on_table: False,
                        holding_b: True,
                    }
                ),
                stack,
            ),
            Step(
                State(
                    {
                        a_clear: False,
                        b_clear: True,
                        a_on_table: True,
                        b_on_a: True,
                    }
                ),
                None,
            ),
        ]
    )

    return TraceList([t1, t2])
