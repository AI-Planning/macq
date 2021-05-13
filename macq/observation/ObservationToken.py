from enum import Enum
from .IdentityToken import IdentityToken


class ObservationToken:
    """
    An ObservationToken object implements a `tokenize` function to generate an
    observation token for an action-state pair.
    """

    class token_method(Enum):
        IDENTITY = 1

    def __init__(
        self,
        method: token_method = token_method.IDENTITY,
    ):
        """
        Creates an ObservationToken object based on the supplied token method
        (defaults to identity). This will store the supplied tokenize method
        to use on steps.
        """
        if method == self.token_method.IDENTITY:
            self = IdentityToken()
