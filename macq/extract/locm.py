""".. include:: ../../docs/templates/extract/observer.md"""


from typing import Dict
from collections import defaultdict

from dataclasses import dataclass

from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .model import Model
from .learned_fluent import LearnedFluent
from ..observation import ActionObservation, ObservedTraceList


@dataclass
class AP:
    """Action + object (argument) position"""

    action_name: str
    pos: int

    def __hash__(self):
        return hash(self.action_name + str(self.pos))


@dataclass
class APState:
    """Object state identifiers"""

    start: int
    end: int


class LOCM:
    """LOCM"""

    def __new__(cls, obs_tracelist: ObservedTraceList):
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

        # initialize state set OS and transition set TS to empty
        ts = set()

        # making OS a dict with AP as key enforces assumption 5
        # (transitions are 1-1 with respect to same action for a given object sort)
        os: Dict[AP, APState] = {}

        ts_objs = defaultdict(list)

        # for actions occurring in seq
        for obs in seq:
            i = obs.index
            action = obs.action
            if action is not None:
                # for each combination of action name A and argument pos P
                for j, obj in enumerate(action.obj_params):
                    # create transition A.P
                    ap = AP(action.name, pos=j + 1)  # NOTE: 1-indexed object position
                    # add state identifiers start(A.P) and end(A.P) to OS
                    os[ap] = APState(i, i + 1)
                    # add A.P to the transition set TS
                    # + collect the set of objects in seq
                    ts_objs[obj].append(ap)

        # for each object
        for obj, trans in ts_objs.items():
            # for each pair of transitions consectutive for obj
            for t1, t2 in zip(trans, trans[1:]):
                # unify states end(t1) and start(t2) in set OS
                os[t2].end = os[t1].start

        # retrieve and flatten set of all transitions
        ts = set(sum(list(ts_objs.values()), []))
        return ts, os
