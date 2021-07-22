from multiprocessing.pool import ThreadPool
from typing import Union


def set_timer_throw_exc(num_seconds: Union[float, int], exception: Exception):
    def timer(function):
        """
        Checks that a function runs within the specified time and raises an exception if it doesn't.

        Args:
            function (function reference):
                The generator function to be wrapped with this time-checker.

        Returns:
            The wrapped function.
        """

        def wrapper(*args, **kwargs):
            pool = ThreadPool(processes=1)

            thr = pool.apply_async(function, args=args, kwds=kwargs)
            # run the function for the specified seconds
            thr.wait(num_seconds)
            # return successful results, if ready
            if thr.ready():
                pool.terminate()
                return thr.get()
            else:
                # otherwise, raise an exception if the function takes too long
                raise exception()

        return wrapper

    return timer


def basic_timer(num_seconds: Union[float, int]):
    def timer(function):
        """
        Runs a function for a specified time.

        Returns:
            The wrapped function.
        """

        def wrapper(*args, **kwargs):
            pool = ThreadPool(processes=1)

            thr = pool.apply_async(function, args=args, kwds=kwargs)
            # run the function for the specified seconds
            thr.wait(num_seconds)
            # return successful results, if ready/if there are any; don't raise an exception otherwise
            if thr.ready():
                pool.terminate()
                return thr.get()
            pool.terminate()

        return wrapper

    return timer


class TraceSearchTimeOut(Exception):
    """
    Raised when the time it takes to generate (or attempt to generate) a single trace is
    longer than the MAX_TRACE_TIME constant. MAX_TRACE_TIME is 30 seconds by default.
    """

    def __init__(
        self,
        message="The generator took longer than MAX_TRACE_TIME in its attempt to generate a trace. "
        + "MAX_TRACE_TIME can be changed through the trace generator used.",
    ):
        super().__init__(message)
