from inspect import signature
from enum import Enum
from typing import Union
from collections.abc import Callable, Sequence


class Action:
    """Placeholder"""

    pass


class Predicate:
    """Placeholder"""

    pass


class token_method(Enum):
    IDENTITY = 1


class ObservationToken:
    """
    An ObservationToken object implements a `tokenize` function to generate an
    observation token for an action-state pair.
    """

    def __init__(
        self,
        method: Union[
            token_method, Callable[[Action, Sequence[Predicate]], tuple]
        ] = token_method.IDENTITY,
    ):
        """
        Creates an ObservationToken object. This will store the supplied
        tokenize method to use on action-state pairs.

        Attributes
        ----------
        tokenize : function
            The function to apply to an action-state pair to generate the
            observation token.
        """
        if isinstance(method, token_method):
            self.tokenize = self.get_method(method)
        else:
            self.tokenize = method

    def get_method(self, method) -> Callable[[Action, Sequence[Predicate]], tuple]:
        """
        Retrieves a predefined `tokenize` function.

        Arguments
        ---------
        method : Enum
            The enum corresponding to the predefined `tokenize` function.

        Returns
        -------
        tokenize : object
            The `tokenize` function reference.
        """

        tokenize = self.identity
        if method == token_method.IDENTITY:
            tokenize = self.identity
        return tokenize

    def identity(self, action: Action, state: Sequence[Predicate]) -> tuple:
        """
        The identity `tokenize` function.

        Arguments
        ---------
        action : Action
            An `Action` object.
        state : list
            An list of fluents representing the state.

        Returns
        -------
        tokenize : function
            The `tokenize` function reference.
        """
        return (action, state)
