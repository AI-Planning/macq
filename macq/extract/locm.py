""".. include:: ../../docs/templates/extract/observer.md"""

from typing import List, Set
from collections import defaultdict

from dataclasses import dataclass
from . import LearnedAction, Model, LearnedFluent, IncompatibleObservationToken
from ..observation import ObservationLists, ActionObservation

# rename ObservationLists -> ObservedTraceList
#         ObservationList -> ObservedTrace


class LOCM:
    """LOCM"""

    def __new__(cls, obs_lists: ObservationLists, debug: bool):
        """Creates a new Model object.

        Args:
            observations (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_lists.type is not ActionObservation:
            raise IncompatibleObservationToken(obs_lists.type, LOCM)
        fluents = LOCM._get_fluents(obs_lists)
        actions = LOCM._get_actions(obs_lists)
        return Model(fluents, actions)

    @staticmethod
    def _get_fluents(obs_lists: ObservationLists):
        """Retrieves the set of fluents in the observations."""
        pass

    @staticmethod
    def _get_actions(obs_lists: ObservationLists):
        """Retrieves and augments the set of actions in the observations."""
        pass
