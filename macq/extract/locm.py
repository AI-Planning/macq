""".. include:: ../../docs/templates/extract/observer.md"""


from typing import Dict, List
from collections import defaultdict

from dataclasses import dataclass

from macq.trace.fluent import PlanningObject

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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, APState):
            return self.start == other.start and self.end == other.end
        return False

    def __hash__(self) -> int:
        return hash((self.start, self.end))


class LOCM:
    """LOCM"""

    def __new__(cls, obs_tracelist: ObservedTraceList, viz=False):
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

        sorts = LOCM._get_sorts(obs_tracelist)
        transitions, obj_states = LOCM._phase1(obs_tracelist)

        if viz:
            graph = LOCM.viz_state_machines(obj_states)
            graph.render(view=True)  # type: ignore

        return Model(fluents, actions)

    @staticmethod
    def _get_sorts(obs_tracelist: ObservedTraceList):
        """Given 2 distinct steps (i & j), if action i = action j
        their list of objects contain the same sorts in the same order

        e.g. open(c1) + open(c2) = c1 and c2 are the same sort

        fetch_jack(j1, c1) ... j's are the same sort AND cs are the same

        need to track what idxs belong to action name

        returns [
                sets containing all objects belonging to sort i
                ]
        """

        sorts = []
        for obs_trace in obs_tracelist:
            seq_sorts = []  # initialize list of sorts for this trace
            seen_actions = {}
            for obs in obs_trace:
                action = obs.action
                if action is not None:
                    if action.name in seen_actions:
                        for sort_idx, obj in zip(
                            seen_actions[action.name], action.obj_params
                        ):
                            seq_sorts[sort_idx].add(obj)
                    else:  # if we haven't seen this action yet
                        idxs = []
                        prev_end = len(seq_sorts) - 1
                        for i, obj in enumerate(action.obj_params):
                            seq_sorts.append(
                                {obj}
                            )  # add a set to the list of sorts for each object
                            idxs.append(
                                prev_end + i + 1
                            )  # track what indexes correspond to this action
                        seen_actions[action.name] = idxs

            sorts.append(seq_sorts)

        return sorts

    @staticmethod
    def _phase1(obs_tracelist: ObservedTraceList):
        seq = obs_tracelist[0]

        # initialize state set OS and transition set TS to empty
        ts = defaultdict(list)
        # making OS a dict with AP as key enforces assumption 5
        # (transitions are 1-1 with respect to same action for a given object sort)
        os: Dict[AP, APState] = {}

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
                    ts[obj].append(ap)

        # for each object
        for obj, trans in ts.items():
            # for each pair of transitions consectutive for obj
            for t1, t2 in zip(trans, trans[1:]):
                # unify states end(t1) and start(t2) in set OS
                os[t2].end = os[t1].start

        return dict(ts), os

    @staticmethod
    def _phase2(obs_tracelist: ObservedTraceList):
        # add the zero argument to each action
        seq = obs_tracelist[0]
        # initialize state set OS and transition set TS to empty
        ts = list()
        # making OS a dict with AP as key enforces assumption 5
        # (transitions are 1-1 with respect to same action for a given object sort)
        os: Dict[AP, APState] = {}
        # for actions occurring in seq
        unique_actions = set()
        for obs in seq:
            i = obs.index
            action = obs.action
            if action is not None:
                if action.name not in unique_actions:
                    ap = AP(action.name, pos=0)
                    os[ap] = APState(i, i + 1)
                    ts.append(ap)

                    unique_actions.add(action.name)

        # for each pair of transitions consectutive for obj
        for t1, t2 in zip(ts, ts[1:]):
            # unify states end(t1) and start(t2) in set OS
            os[t2].end = os[t1].start

        if len(os) == 1:
            # For Muise:
            # Are we expecting an empty finite state here?
            # ---> why is is not length one
            # ---> is the equate proper
            return None, None
        return ts, os

    @staticmethod
    def viz_state_machines(ts: Dict[PlanningObject, List[AP]], os: Dict[AP, APState]):
        from graphviz import Digraph

        state_machines = []

        for obj, trans in ts.items():
            graph = Digraph(f"LOCM-phase1-{obj.name}")
            for i, ap in enumerate(trans):
                graph.node(str(i), label=f"{obj.name}state{i}", shape="oval")
                if i > 0:
                    graph.edge(str(i), str(i - 1))

            state_machines.append(graph)

        return state_machines
