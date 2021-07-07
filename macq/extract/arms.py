import macq.extract as extract
from ..observation import PartialObservation
from ..trace import ObservationLists


class ARMS:
    """ARMS model extraction method.

    Extracts a Model from state observations using the ARMS technique. Fluents
    are retrieved from the initial state. Actions are learned using the
    algorithm.
    """

    def __new__(cls, obs_lists: ObservationLists):
        if obs_lists.type is not PartialObservation:
            raise extract.IncompatibleObservationToken(obs_lists.type, ARMS)
