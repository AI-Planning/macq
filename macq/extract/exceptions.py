class IncompatibleObservationToken(Exception):
    def __init__(self, token, technique, message=None):
        if message is None:
            message = f"Observations of type {token.__name__} are not compatible with the {technique.__name__} extraction technique."
        super().__init__(message)


class InconsistentConstraintWeights(Exception):
    def __init__(self, constraint, weight1, weight2, message=None):
        if message is None:
            message = f"Tried to assign the constraint {constraint} conflicting weights ({weight1} and {weight2})."
        super().__init__(message)


class InvalidMaxSATModel(Exception):
    def __init__(self, model, message=None):
        if message is None:
            message = f"The MAX-SAT solver generated an invalid model. Model should be a list of integers. model = {model}."
        super().__init__(message)


class ConstraintContradiction(Exception):
    def __init__(self, relation, effect, action, message=None):
        if message is None:
            message = f"Action model has contradictory constraints for {relation}'s presence in the {effect} list of {action.details()}."
        super().__init__(message)
