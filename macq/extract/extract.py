from dataclasses import dataclass
from enum import Enum, auto

from . import Model
from ..trace import ObservationLists, Action, State

# Techniques
from .observer import Observer
from .slaf import Slaf
from .arms import ARMS


@dataclass
class SAS:
    pre_state: State
    action: Action
    post_state: State


class IncompatibleObservationToken(Exception):
    def __init__(self, token, technique, message=None):
        if message is None:
            message = f"Observations of type {token.__name__} are not compatible with the {technique.__name__} extraction technique."
        super().__init__(message)


class modes(Enum):
    """Model extraction techniques.

    An Enum where each value represents a model extraction technique.
    """

    OBSERVER = auto()
    SLAF = auto()
    ARMS = auto()


class Extract:
    """Extracts models from observations.

    The Extract class uses an extraction method to retrieve an action Model
    from state observations.
    """

    def __new__(cls, obs_lists: ObservationLists, mode: modes) -> Model:
        """Extracts a Model object.

        Extracts a model from the observations using the specified extraction
        technique.

        Args:
            obs_lists (ObservationList):
                The state observations to extract the model from.
            mode (Enum):
                The extraction technique to use.

        Returns:
            A Model object. The model's characteristics are determined by the
            extraction technique used.
        """
        techniques = {
            modes.OBSERVER: Observer,
            modes.SLAF: Slaf,
            modes.ARMS: ARMS,
        }
        if mode == modes.SLAF:
            # only allow one trace
            assert (
                len(obs_lists) == 1
            ), "The SLAF extraction technique only takes one trace."

        return techniques[mode](obs_lists)
