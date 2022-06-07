from . import InvalidNumberOfTraces, InvalidPlanLength


def set_num_traces(num_traces: int):
    """Checks the validity of the number of traces and then sets it.

    Args:
        num_traces (int):
            The number of traces to set.

    Raises:
        InvalidNumberOfTraces:
            The exception raised when the number of traces provided is invalid.
    """
    if num_traces >= 0:
        return num_traces
    else:
        raise InvalidNumberOfTraces()


def set_plan_length(plan_len: int):
    """Checks the validity of the plan length and then sets it.

    Args:
        plan_len (int):
            The plan length to set.

    Raises:
        InvalidPlanLength:
            The exception raised when the plan length provided is invalid.
    """
    if plan_len > 0:
        return plan_len
    else:
        raise InvalidPlanLength()
