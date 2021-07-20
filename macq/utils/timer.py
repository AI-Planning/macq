from multiprocessing.pool import ThreadPool
from typing import Union


def set_timer(num_seconds: Union[float, int], exception: Exception):
    def timer(generator):
        """
        Checks that a trace is generated within the time indicated by the MAX_TRACE_TIME
        constant in the respective generator.

        Args:
            generator (function reference):
                The generator function to be wrapped with this time-checker.

        Returns:
            The wrapped generator function.
        """

        def wrapper(*args, **kwargs):
            pool = ThreadPool(processes=1)

            thr = pool.apply_async(generator, args=args, kwds=kwargs)
            # run the function for the specified seconds
            thr.wait(num_seconds)
            # return a successful trace, if ready
            if thr.ready():
                pool.terminate()
                return thr.get()
            else:
                # otherwise, raise an exception if the function takes too long
                raise exception()

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
