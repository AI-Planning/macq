import time
from typing import Union


class Deadline:
    """
    A time limit that a search checks for itself between its steps.

    The search runs in the caller's thread, so it really stops once it sees the
    deadline has passed. A step that is already running, such as a planner call,
    can finish past the deadline.
    """

    def __init__(self, num_seconds: Union[float, int]):
        self.num_seconds = num_seconds
        self._end = time.monotonic() + num_seconds

    def passed(self) -> bool:
        return time.monotonic() >= self._end


class TraceSearchTimeOut(Exception):
    """
    Raised when the time it takes to generate (or attempt to generate) a single trace is
    longer than the generator's `max_time` attribute.
    """

    def __init__(self, max_time: float):
        message = f"The generator could not find a suitable trace in {max_time} seconds or less. Change the `max_time` attribute for the trace generator used if you would like to have more time to generate a trace."
        super().__init__(message)


class InvalidTime(Exception):
    """
    Raised when the user supplies an invalid maximum time for a trace to be generated
    to a generator.
    """

    def __init__(
        self,
        message="The provided maximum time is invalid.",
    ):
        super().__init__(message)
