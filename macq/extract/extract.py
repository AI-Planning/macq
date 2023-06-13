""".. include:: ../../docs/templates/extract/extract.md"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Union

from ..observation import ObservedTraceList
from ..trace import Action, State
from .model import Model

from .amdn import AMDN
from .arms import ARMS
from .locm import LOCM
from .slaf import SLAF
from .observer import Observer

@dataclass
class SAS:
    pre_state: State
    action: Action
    post_state: State


class modes(Enum):
    """Model extraction techniques.

    An Enum where each value represents a model extraction technique.
    """

    OBSERVER = auto()
    SLAF = auto()
    AMDN = auto()
    ARMS = auto()
    LOCM = auto()


class Extract:
    """Extracts models from observations.

    The Extract class uses an extraction method to retrieve an action Model
    from state observations.
    """

    def __new__(
        cls,
        obs_tracelist: ObservedTraceList,
        mode: modes,
        debug: Union[bool, Dict[str, bool], List[str]] = False,
        **kwargs
    ) -> Model:
        """Extracts a Model object.

        Extracts a model from the observations using the specified extraction
        technique.

        Args:
            obs_tracelist (ObservationList):
                The state observations to extract the model from.
            mode (Enum):
                The extraction technique to use.
            debug (bool, dict, list):
                Model specific debugging options. Either a boolean, or a list/dict indicating the functions to debug.
            **kwargs: (keyword arguments)
                Any extra arguments to supply to the extraction technique.

        Returns:
            A Model object. The model's characteristics are determined by the
            extraction technique used.
        """

        if len(obs_tracelist) == 0:
            raise ValueError("ObservationList is empty. Nothing to extract from.")

        techniques = {
            modes.OBSERVER: Observer,
            modes.SLAF: SLAF,
            modes.AMDN: AMDN,
            modes.ARMS: ARMS,
            modes.LOCM: LOCM,
        }
        return techniques[mode](obs_tracelist, debug=debug, **kwargs)
