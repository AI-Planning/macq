from enum import Enum
from inspect import signature


class InvalidMethod(Exception):
    def __init__(self, method, message="Invalid method."):
        self.method = method
        self.message = message
        super().__init__(self.message)


class token_method(Enum):
    IDENTITY = 1


class ObservationToken:
    def __init__(self, method=token_method.IDENTITY):
        if isinstance(method, token_method):
            self.tokenize = self.get_method(method)
        elif callable(method):
            # more checking to make sure the method is a proper tokenizer?
            if not len(signature(method).parameters) == 2:
                raise InvalidMethod(method)
            self.tokenize = method
        else:
            raise InvalidMethod(method)

    def get_method(self, method):
        if method == token_method.IDENTITY:
            return self.identity

    def identity(self, action, state):
        return (action, state)
