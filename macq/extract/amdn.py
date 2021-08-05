import macq.extract as extract
from .model import Model
from ..observation import NoisyPartialDisorderedParallelObservation

class AMDN:
    def __new__(cls, obs_lists: ObservationLists):
        """Creates a new Model object.

        Args:
            obs_lists (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_lists.type is not NoisyPartialDisorderedParallelObservation:
            raise extract.IncompatibleObservationToken(obs_lists.type, AMDN)
        #return Model(fluents, actions)

    def __build_disorder_constraints(self):
        pass

    def __build_parallel_constraints(self):
        pass

    def __build_noise_constraints(self):
        pass

    def __solve_constraints(self):
        pass

    def __convert_to_model(self):
        pass