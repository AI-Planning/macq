""".. include:: ../../docs/templates/extract/observer.md"""


from typing import List, Set
from collections import defaultdict

from attr import dataclass

from macq.trace.fluent import PlanningObject
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .model import Model
from .learned_fluent import LearnedFluent
from ..observation import ActionObservation, ObservationLists

# rename ObservationLists -> ObservedTraceList
#         ObservationList -> ObservedTrace


@dataclass
class AP:
    """Action + object (argument) position"""

    action_name: str
    pos: int

    def __hash__(self) -> int:
        return hash(self.action_name + str(self.pos) + str(self.start))


@dataclass
class OS:
    """Object state"""

    ap: AP
    obj: PlanningObject
    start: str
    end: str


class LOCM:
    """LOCM"""

    def __new__(cls, obs_tracelist: ObservationLists, debug: bool):
        """Creates a new Model object.

        Args:
            observations (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_tracelist.type is not ActionObservation:
            raise IncompatibleObservationToken(obs_tracelist.type, LOCM)

        fluents, actions = None, None
        state_machines = LOCM._phase1(obs_tracelist)

        return Model(fluents, actions)

    @staticmethod
    def _phase1(obs_tracelist: ObservationLists):
        seq = obs_tracelist[0]
        n = len(seq)
        ts = []
        os = []
        obj_state_ind = defaultdict(int)
        for obs in seq:
            action = obs.action
            if action:
                i = obs.index
                for j, obj in enumerate(action.obj_params):
                    ap = AP(action.name, j)
                    # if ap already in ts, use start = prev.start
                    # === don't add to os?
                    os.append(
                        OS(
                            ap,
                            obj,
                            f"{obj.obj_type}state{str(obj_state_ind[obj.obj_type])}",
                            f"{obj.obj_type}state{str(obj_state_ind[obj.obj_type] + 1)}",
                        )
                    )
                    ts.append(ap)
                    obj_state_ind[obj.obj_type] += 1
                    # missing assumption 5
