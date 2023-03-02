""".. include:: ../../docs/templates/extract/observer.md"""


from collections import defaultdict
from dataclasses import dataclass
from pprint import pprint
from typing import Dict, List, Set

from macq.trace.fluent import PlanningObject

from ..observation import ActionObservation, ObservedTraceList
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .learned_fluent import LearnedFluent
from .model import Model


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
        # TODO: use sorts in phase 1
        transitions, obj_states = LOCM._phase1(obs_tracelist, sorts)

        if viz:
            graph = LOCM.viz_state_machines(obj_states)
            graph.render(view=True)  # type: ignore

        return Model(fluents, actions)

    @staticmethod
    def _get_sorts(obs_tracelist: ObservedTraceList) -> List[Dict[str, int]]:
        """Given 2 distinct steps (i & j), if action i = action j
        their list of objects contain the same sorts in the same order


        Example 1:
            open(c1); fetch jack(j1,c1); fetch wrench(wr1,c1); close(c1); open(c2);
            fetch wrench(wr2,c2); fetch jack(j2,c2); close(c2); open(c3); close(c3)

            This trace is composed of 3 sorts {c1, c2, c3}, {wr1, wr2}, {j1,j2}.

        Extension:
            open(c1); fetch jack(j1,c1); fetch wrench(wr1,c1); close(c1); open(c2);
            fetch wrench(wr2,c2); fetch jack(j2,c2); close(c2); open(c3); close(c3);
            close(wr1);

            In this case, the final action close(wr1) would unite the container
            and wrench sorts into one. Therefore the trace is composed of 2
            sorts {c1, c2, c3, wr1, wr2}, {j1,j2}.
        """

        sorts = []
        for obs_trace in obs_tracelist:
            seq_sorts = []  # initialize list of sorts for this trace
            # track actions seen in the trace, and the sort each actions params belong to
            seen_actions: Dict[str, List[int]] = {}
            # track objects seen in the trace, and the sort each belongs to
            seen_objs: Dict[str, int] = {}

            for obs in obs_trace:
                action = obs.action
                if action is not None:

                    if action.name not in seen_actions:  # new action
                        idxs = []  # idxs[i] stores the sort of action param i
                        # for each parameter of the action
                        for obj in action.obj_params:

                            if obj.name not in seen_objs:  # new object
                                # append a sort (set) containing the object
                                seq_sorts.append({obj})
                                # record the object has been seen and the index of the sort it belongs to
                                obj_sort_idx = len(seq_sorts) - 1
                                seen_objs[obj.name] = obj_sort_idx
                                idxs.append(obj_sort_idx)

                            else:  # object already has a sort, don't append a new one
                                # look up the sort of the object
                                idxs.append(seen_objs[obj.name])

                        # record the index of the sort of the action's parameters
                        seen_actions[action.name] = idxs

                    else:  # action seen before

                        for action_sort_idx, obj in zip(
                            seen_actions[action.name], action.obj_params
                        ):
                            # action_sort_idx -> sort of current action parameter
                            # obj -> object that is action parameter ap

                            if obj.name not in seen_objs:  # new object
                                # add the object to the sort of current action parameter
                                seq_sorts[action_sort_idx].add(obj)

                            else:  # object already has a sort
                                # retrieve the sort the object belongs to
                                obj_sort_idx = seen_objs[obj.name]

                                # check if the object's sort matches the action paremeter's
                                # if so, do nothing and move on to next step
                                if obj_sort_idx != action_sort_idx:  # else
                                    # unite the action parameter's sort and the object's sort
                                    seq_sorts[action_sort_idx] = seq_sorts[
                                        action_sort_idx
                                    ].union(seq_sorts[obj_sort_idx])

                                    # drop the not unionized sort
                                    seq_sorts.pop(obj_sort_idx)

                                    # update all outdated records of which sort the affected objects belong to

                                    for action_name, idxs in seen_actions.items():
                                        for i, idx in enumerate(idxs):
                                            if idx == obj_sort_idx:
                                                seen_actions[action_name][
                                                    i
                                                ] = action_sort_idx

                                    for seen_obj, idx in seen_objs.items():
                                        if idx == obj_sort_idx:
                                            seen_objs[seen_obj] = action_sort_idx
            # end
            sorts.append(seq_sorts)

        obj_sorts_list = []
        for seq_sorts in sorts:
            obj_sorts = {}
            for i, sort in enumerate(seq_sorts):
                for obj in sort:
                    obj_sorts[obj.name] = i
            obj_sorts_list.append(obj_sorts)

        return obj_sorts_list

    @staticmethod
    def _phase1(obs_tracelist: ObservedTraceList, sorts_list: List[Dict[str, int]]):
        seq = obs_tracelist[0]
        sorts = sorts_list[0]

        sort_traces = defaultdict(list)
        # for actions occurring in seq
        for obs in seq:
            # i = obs.index
            action = obs.action
            if action is not None:
                # for each combination of action name A and argument pos P
                for j, obj in enumerate(action.obj_params):
                    sort = sorts[obj.name]
                    # create transition A.P
                    ap = AP(action.name, pos=j + 1)  # NOTE: 1-indexed object position
                    sort_traces[sort].append(ap)

        # TODO: outer loop HERE
        # only on containers
        state_n = 1
        ap_state_pointers: Dict[AP, APState] = {}
        os: List[Set[int]] = []
        prev_states: APState = None  # type: ignore
        for ap in sort_traces[0]:
            if ap not in ap_state_pointers:
                ap_state_pointers[ap] = APState(state_n, state_n + 1)
                state_n += 2

                os.append({ap_state_pointers[ap].start})
                os.append({ap_state_pointers[ap].end})

            if prev_states is not None:
                states = ap_state_pointers[ap]

                # get the indexes of the state sets containing the start state and prev end state
                state_idx, prev_idx = None, None
                for j, state_set in enumerate(os):
                    if states.start in state_set:
                        state_idx = j
                    if prev_states.end in state_set:
                        prev_idx = j
                    if state_idx is not None and prev_idx is not None:
                        break

                # impossible, but the linter doesn't know that
                assert (
                    state_idx is not None and prev_idx is not None
                ), f"Start state ({states.start}) or prev end state ({prev_states.end}) is not in ts"

                # if not the same state set, merge the two
                if state_idx != prev_idx:
                    print(f"** merging {os[state_idx]} with {os[prev_idx]}")
                    os[state_idx] = os[state_idx].union(os[prev_idx])
                    os.pop(prev_idx)

                print(os)

            prev_states = ap_state_pointers[ap]

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
