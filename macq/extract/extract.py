""".. include:: ../../docs/templates/extract/extract.md"""

from dataclasses import dataclass
from enum import Enum, auto
from ..trace import Action, State
from ..observation import ObservationLists
from .model import Model
from .observer import Observer
from .slaf import SLAF
from .amdn import AMDN
from .arms import ARMS
from .bglearner import BGLearner


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
    BGLearner=auto()


class Extract:
    """Extracts models from observations.

    The Extract class uses an extraction method to retrieve an action Model
    from state observations.
    """

    def __new__(
        cls, obs_lists: ObservationLists, mode: modes, debug: bool = False, **kwargs
    ) -> Model:
        """Extracts a Model object.

        Extracts a model from the observations using the specified extraction
        technique.

        Args:
            obs_lists (ObservationList):
                The state observations to extract the model from.
            mode (Enum):
                The extraction technique to use.
            **kwargs: (keyword arguments)
                Any extra arguments to supply to the extraction technique.

        Returns:
            A Model object. The model's characteristics are determined by the
            extraction technique used.
        """
        techniques = {
            modes.OBSERVER: Observer,
            modes.SLAF: SLAF,
            modes.AMDN: AMDN,
            modes.ARMS: ARMS,
            modes.BGLearner: BGLearner

        }
        if mode == modes.SLAF:
            if len(obs_lists) != 1:
                raise Exception("The SLAF extraction technique only takes one trace.")

        return techniques[mode](obs_lists, debug, **kwargs)
