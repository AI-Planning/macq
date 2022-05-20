class TokenizationError(Exception):
    def __init__(self, token, message=None):
        if message is None:
            message = (
                f"Tokenization to Observation type {token.__name__} must happen at the trace level, not the step level.",
            )
            "Use a TraceList with this Trace for proper tokenization."
        super().__init__(message)
