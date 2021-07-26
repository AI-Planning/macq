class IncompatibleObservationToken(Exception):
    def __init__(self, token, technique, message=None):
        if message is None:
            message = f"Observations of type {token.__name__} are not compatible with the {technique.__name__} extraction technique."
        super().__init__(message)


class InconsistentConstraintWeights(Exception):
    def __init__(self, constraint, weight1, weight2, message=None):
        if message is None:
            message = f"Tried to assign the constraint {constraint} conflicting weights ({weight1} and {weight2})"
        super().__init__()
