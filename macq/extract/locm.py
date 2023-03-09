""".. include:: ../../docs/templates/extract/locm.md"""


from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from ..observation import ActionObservation, Observation, ObservedTraceList
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
class APStates:
    """Pointers to the start and end states for an A.P"""

    start: int
    end: int


Sorts = Dict[str, int]
OSType = Dict[int, List[Set[int]]]
TSType = Dict[int, Dict[AP, APStates]]


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

        assert len(obs_tracelist) == 1, "Temp only allowing 1 trace"
        obs_trace = obs_tracelist[0]

        fluents, actions = None, None

        sorts = LOCM._get_sorts(obs_trace)
        # TODO: use sorts in phase 1
        TS, OS = LOCM._phase1(obs_trace, sorts)

        if viz:
            graph = LOCM.viz_state_machines(TS, OS, sorts)
            graph.render(view=True)  # type: ignore

        return Model(fluents, actions)

    @staticmethod
    def _get_sorts(obs_trace: List[Observation]) -> Sorts:
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

        obj_sorts = {}
        for i, sort in enumerate(seq_sorts):
            for obj in sort:
                # 1-indexed so the zero-object can be sort 0
                obj_sorts[obj.name] = i + 1

        return obj_sorts

    @staticmethod
    def _phase1(obs_trace: List[Observation], sorts: Sorts) -> Tuple[TSType, OSType]:
        """Phase 1: Create a state machine for each object sort

        Args:
            obs_tracelist (ObservedTraceList):
                List of observed traces
            sorts_list (List[Dict[str, int]]):
                List of object sorts for each trace.

        Returns:
            TS (Dict[int, Dict[AP, APState]]):
                Set of transitions for each object sort.
            OS (Dict[int, List[Set[int]]]):
                Set of distinct states for each object sort.
        """

        # collect traces for each sort (filtering out steps irrelevant to the sort)
        sort_traces = defaultdict(list)
        for obs in obs_trace:
            action = obs.action
            if action is not None:
                # for each combination of action name A and argument pos P
                sort_traces[0].append(AP(action.name, pos=0))  # add the zero-object
                for j, obj in enumerate(action.obj_params):
                    sort = sorts[obj.name]
                    # create transition A.P
                    ap = AP(action.name, pos=j + 1)  # NOTE: 1-indexed object position
                    sort_traces[sort].append(ap)

        # get unique states and transitions for each sort from the filtered traces
        OS = {}
        TS = {}
        for sort, seq in sort_traces.items():
            state_n = 1
            ap_state_pointers: Dict[AP, APStates] = {}
            os: List[Set[int]] = []
            prev_states: APStates = None  # type: ignore
            for ap in seq:
                if ap not in ap_state_pointers:
                    ap_state_pointers[ap] = APStates(state_n, state_n + 1)
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
                        os[state_idx] = os[state_idx].union(os[prev_idx])
                        os.pop(prev_idx)

                prev_states = ap_state_pointers[ap]

            # Don't add the zero-object if it only has one state
            if not (sort == 0 and len(os) == 1):
                TS[sort] = ap_state_pointers
                OS[sort] = os

        return TS, OS

    @staticmethod
    def viz_state_machines(TS: TSType, OS: OSType):
        from graphviz import Digraph

        print("TS:", TS, end="\n\n")
        print("OS:", OS)

        state_machines = []

        for (sort, trans), states in zip(TS.items(), OS.values()):
            graph = Digraph(f"LOCM-phase1-sort{sort}")
            for i in range(len(states)):
                graph.node(str(i), label=f"state{i}", shape="oval")
            for ap, apstate in trans.items():
                start_idx = None
                end_idx = None
                for i, state_set in enumerate(states):
                    if apstate.start in state_set:
                        start_idx = i
                    if apstate.end in state_set:
                        end_idx = i
                    if start_idx is not None and end_idx is not None:
                        break
                graph.edge(
                    str(start_idx), str(end_idx), label=f"{ap.action_name}.{ap.pos}"
                )

            state_machines.append(graph)

        return state_machines

    @staticmethod
    def _phase3():
        """
        consider wrench_state0 for wrench sort + actions:
            putaway_wrench(wrench, container) -> wrench_state0
            fetch_wrench(wrench, container) -> wrench_state1

        the consectutive actions in any sequence have the same value for the container param
        therefore, wrench_state0 has a state variable for container

        this doesn't hold for wrench_state1, since there may


        In general:
            If there are two consectutive transitions for a given object sort
            and there is a parameter that is the same for both actions,
            and this is consistent across all sequences,
            then the intermediate state is parameterized by this other sort.
        """
        pass
