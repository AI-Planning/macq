import time
from multiprocessing.pool import ThreadPool

MAX_TIME = 30.0

def timer(generator, num_seconds=MAX_TIME):
    """
    Checks that a trace is generated within the time indicated by the MAX_TIME
    constant.

    Arguments
    ---------
    generator : function reference
        The generator function to be wrapped with this time-checker.
    """
    def wrapper(*args, **kwargs):
        pool = ThreadPool(processes=1)
        # start the timer
        begin = time.perf_counter()
        current = begin
        thr = pool.apply_async(generator, args=args, kwds=kwargs)
        # continue counting time while the function has not completed
        while not thr.ready(): 
            current = time.perf_counter()
            # raise exception if the function takes too long
            if current - begin > num_seconds:
                raise TraceSearchTimeOut()
        # return a successful trace
        return thr.get()
    return wrapper

class TraceSearchTimeOut(Exception):
        """
        Raised when the time it takes to generate (or attempt to generate) a single trace is 
        longer than the MAX_TIME constant. MAX_TIME is 30 seconds by default.
        """

        def __init__(
            self,
            message="The generator function took longer than MAX_TIME in its attempt to generate a trace."
        ):
            super().__init__(message)
