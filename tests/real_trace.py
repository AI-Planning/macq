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
    pick_up_a = Action("pick up A", [blockA])
    pick_up_b = Action("pick up B", [blockB])
    put_down_a = Action("put down A", [blockA])
    put_down_b = Action("put down B", [blockB])
    stack_a_b = Action("stack A on B", [blockA, blockB])
    stack_b_a = Action("stack B on A", [blockB, blockA])

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
                pick_up_a,
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
                stack_a_b,
            ),
            Step(
                State(
                    {
                        a_clear: True,
                        b_clear: False,
                        b_on_table: True,
                        a_on_b: True,
                        holding_a: False,
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
                pick_up_b,
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
                stack_b_a,
            ),
            Step(
                State(
                    {
                        a_clear: False,
                        b_clear: True,
                        a_on_table: True,
                        b_on_a: True,
                        holding_b: False,
                    }
                ),
                None,
            ),
        ]
    )

    return TraceList([t1, t2])
