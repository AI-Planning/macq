class PercentError(Exception):
    """Raised when the user attempts to supply an invalid percentage of fluents to hide."""

    def __init__(
        self,
        message="The percentage supplied is invalid.",
    ):
        super().__init__(message)
