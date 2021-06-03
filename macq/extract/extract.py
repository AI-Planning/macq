from dataclasses import dataclass
from typing import List, Set
from enum import Enum, auto
from .observer import Observer
from ..observation import Observation
from ..trace import ObservationList, Action, State


@dataclass
class SAS:
    pre_state: State
    action: Action
    post_state: State


class IncompatibleObservationToken(Exception):
    def __init__(
        self,
        message="The observations are not compatible with the extraction technique.",
    ):
        super().__init__(message)


class modes(Enum):
    """Model extraction techniques.

    An Enum where each value represents a model extraction technique.
    """

    OBSERVER = auto()


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
        if mode == modes.OBSERVER:
            return Observer(observations)

    @staticmethod
    def get_transitions(action: Action, observations: List[List[Observation]]):
        sas_triples = []
        trace_obs: List[Observation]
        for trace_obs in observations:
            for obs in trace_obs:
                if obs.step.action == action:
                    triple = SAS(
                        obs.step.state, action, trace_obs[obs.index + 1].step.state
                    )
                    sas_triples.append(triple)
        return sas_triples
