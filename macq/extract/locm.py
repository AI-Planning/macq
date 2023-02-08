""".. include:: ../../docs/templates/extract/observer.md"""


from typing import List, Set
from collections import defaultdict

from dataclasses import dataclass

from macq.trace.fluent import PlanningObject
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .model import Model
from .learned_fluent import LearnedFluent
from ..observation import ActionObservation, ObservedTraceList

# rename ObservationLists -> ObservedTraceList
#         ObservationList -> ObservedTrace


@dataclass
class AP:
    """Action + object (argument) position"""

    action_name: str
    pos: int

    def __hash__(self):
        return hash(self.action_name + str(self.pos))


@dataclass
class OS:
    """Object state"""

    ap: AP
    obj: PlanningObject
    start: str
    end: str

    def __hash__(self):
        # hash using only A.P to enforce assumption 5: the name of each action
        # restricted to any of its transitions forms a 1-1 map between object
        # states
        return hash(self.ap)


class LOCM:
    """LOCM"""

    def __new__(cls, obs_tracelist: ObservedTraceList, debug: bool):
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
    def _phase1(obs_tracelist: ObservedTraceList):
        seq = obs_tracelist[0]
        ts = set()
        os = set()
        os_objs = defaultdict(set)
        obj_state_ind = defaultdict(int)
        for obs in seq:
            action = obs.action
            if action:
                i = obs.index
                for j, obj in enumerate(action.obj_params):
                    ap = AP(action.name, j + 1)  # 1-indexed object position
                    # os.append(
                    os_objs[obj].add(
                        OS(
                            ap,
                            obj,
                            f"{obj.obj_type}state{str(obj_state_ind[obj.obj_type])}",
                            f"{obj.obj_type}state{str(obj_state_ind[obj.obj_type] + 1)}",
                        )
                    )
                    ts.add(ap)
                    obj_state_ind[obj.obj_type] += 1

        for obj in os_objs:
            actions = set()
            remove = set()
            for t in os_objs[obj]:
                if t.ap in actions:
                    remove.add(t.ap)
                else:
                    actions.add(t.ap)
            for ap in remove:
                os_objs[obj].remove(ap)

        # >>>>>>>>>>>>>>>>>>>>>>>
        from IPython import embed

        embed()
        # >>>>>>>>>>>>>>>>>>>>>>>

        os = {t for obj in os_objs for t in os_objs[obj]}

        return ts, os
