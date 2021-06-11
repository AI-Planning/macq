class InvalidPlanLength(Exception):
    """
    Raised when the user attempts to create a trace of an invalid length.
    """

    def __init__(
        self,
        message="The provided length of the trace is invalid.",
    ):
        super().__init__(message)


class InvalidNumberOfTraces(Exception):
    """
    Raised when the user attempts to create an invalid number of traces.
    """

    def __init__(
        self,
        message="The provided number of traces is invalid.",
    ):
        super().__init__(message)
