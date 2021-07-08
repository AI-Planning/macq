from typing import Set, List
import macq.extract as extract
from ..observation import PartialObservation
from ..trace import ObservationLists, Fluent


class ARMS:
    """ARMS model extraction method.

    Extracts a Model from state observations using the ARMS technique. Fluents
    are retrieved from the initial state. Actions are learned using the
    algorithm.
    """

    def __new__(cls, obs_lists: ObservationLists):
        if obs_lists.type is not PartialObservation:
            raise extract.IncompatibleObservationToken(obs_lists.type, ARMS)

        # assert that there is a goal
        ARMS._check_goal(obs_lists)
        # get fluents from initial state
        fluents = ARMS._get_fluents(obs_lists)
        # call algorithm to get actions
        actions = ARMS._get_actions(obs_lists)
        return extract.Model(fluents, actions)

    @staticmethod
    def _check_goal(obs_lists: ObservationLists) -> bool:
        """Checks that there is a goal state in the ObservationLists."""
        goal = False
        obs_list: List[PartialObservation]
        for obs_list in obs_lists:
            obs = obs_list[-1]
            # if obs.step.state
        return goal

    @staticmethod
    def _get_fluents(obs_lists: ObservationLists) -> Set[Fluent]:
        """Retrieves the set of fluents in the observations."""
        fluents = set()
        obs_list: List[PartialObservation]
        for obs_list in obs_lists:
            pass

        return fluents

    @staticmethod
    def _get_actions(obs_lists: ObservationLists) -> Set[str]:
        pass
