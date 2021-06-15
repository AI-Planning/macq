from multiprocessing.pool import ThreadPool


def set_timer(num_seconds):
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
                raise TraceSearchTimeOut()

        return wrapper

    return timer


class TraceSearchTimeOut(Exception):
    """
    Raised when the time it takes to generate (or attempt to generate) a single trace is
    longer than the MAX_TIME constant. MAX_TIME is 30 seconds by default.
    """

    def __init__(
        self,
        message="The generator function took longer than MAX_TIME in its attempt to generate a trace."
        + "MAX_TIME can be changed through macq.utils.timer.MAX_TIME.",
    ):
        super().__init__(message)


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    from pathlib import Path
    from macq.generate.pddl import VanillaSampling

    vanilla = VanillaSampling(problem_id=123, plan_len=20, num_traces=100)
