from dataclasses import dataclass
from typing import List
from enum import Enum, auto
from .observer import Observer
from .slaf import Slaf
from ..observation import Observation
from ..trace import ObservationList, Action, State


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


class Extract:
    """Extracts models from observations.

    The Extract class uses an extraction method to retrieve an action Model
    from state observations.
    """

    def __new__(cls, observations: ObservationList, mode: modes):
        """Extracts a Model object.

        Extracts a model from the observations using the specified extraction
        technique.

        Args:
            observations (ObservationList):
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
        }
        if mode == modes.SLAF:
            # only allow one trace
            assert (
                len(observations) == 1
            ), "Only 1 trace is allowed with the current implementation."

        return techniques[mode](observations)
