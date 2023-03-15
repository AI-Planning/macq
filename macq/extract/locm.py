""".. include:: ../../docs/templates/extract/locm.md"""


from collections import defaultdict
from collections.abc import Set as SetClass
from dataclasses import asdict, dataclass
from pprint import pprint
from typing import Dict, List, NamedTuple, Set, Tuple, Union

from macq.trace.action import Action
from macq.trace.fluent import PlanningObject

from ..observation import ActionObservation, Observation, ObservedTraceList
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .learned_fluent import LearnedFluent
from .model import Model

# Phase 1 types


@dataclass
class AP:
    """Action.Position (of object parameter)"""

    action: Action
    pos: int

    def __hash__(self):
        return hash(self.action.name + str(self.pos))
        # return hash((self.action, self.pos))

    def __eq__(self, other):
        return hash(self) == hash(other)


APStates = NamedTuple("APStates", [("start", int), ("end", int)])
Sorts = Dict[str, int]
APStatePointers = Dict[int, Dict[AP, APStates]]


class FSMState(SetClass):
    def __init__(self, iterable):
        self._data: Set[int] = set(iterable)

    def __contains__(self, value):
        return value in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:
        return self._data.__repr__()

    def union(self, other):
        assert isinstance(other, FSMState), "Can only union FSMState with FSMState"
        return FSMState(self._data.union(other._data))


OSType = Dict[int, List[FSMState]]
TSType = Dict[int, Dict[PlanningObject, List[AP]]]

# Phase 3 types


@dataclass
class HSIndex:
    B: AP
    k: int
    C: AP
    l: int

    def __hash__(self) -> int:
        # NOTE: AP is hashed by action name + pos
        # i.e. the same actions but operating on different objects (in the same pos)
        # will be hashed the same
        # This prevents duplicate hypotheses for an A.P pair
        # e.g. B1=AP(action=<action on G obj1>, pos=1), B2=AP(action=<action on G obj2>, pos=1)
        # with the same k,l, and C (similarly for C) will be hashed the same
        return hash(
            (
                self.B,
                self.k,
                self.C,
                self.l,
            )
        )


@dataclass
class HSItem:
    S: int
    k_: int
    l_: int
    G: int
    G_: int
    supported: bool

    def __hash__(self) -> int:
        return hash((self.S, self.k_, self.l_, self.G, self.G_))


@dataclass
class Hypothesis:
    S: int
    B: AP
    k: int
    k_: int
    C: AP
    l: int
    l_: int
    G: int
    G_: int

    def __hash__(self) -> int:
        return hash(
            (
                self.S,
                self.B,
                self.k,
                self.k_,
                self.C,
                self.l,
                self.l_,
                self.G,
                self.G_,
            )
        )

    @staticmethod
    def from_dict(hs: Dict[HSIndex, Set[HSItem]]):
        """Converts a dict of HSIndex -> HSItem to a set of Hypothesis"""
        HS = set()
        for hsind, hsitems in hs.items():
            hsind = hsind.__dict__
            for hsitem in hsitems:
                hsitem_dict = hsitem.__dict__
                hsitem_dict.pop("supported")
                HS.add(Hypothesis(**{**hsind, **hsitem_dict}))
        return HS


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
        TS, ap_state_pointers, OS = LOCM._phase1(obs_trace, sorts)

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
            and wrench sorts into one. Therefore this trace is composed of 2
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
    def _get_states(states, pointer, pointer2) -> Tuple[int, int]:
        state1, state2 = None, None
        for i, state_set in enumerate(states):
            if pointer in state_set:
                state1 = i
            if pointer2 in state_set:
                state2 = i
            if state1 is not None and state2 is not None:
                break

        assert state1 is not None, f"Pointer ({pointer}) not in states: {states}"
        assert state2 is not None, f"Pointer ({pointer2}) not in states: {states}"
        return state1, state2

    @staticmethod
    def _phase1(
        obs_trace: List[Observation], sorts: Sorts
    ) -> Tuple[TSType, APStatePointers, OSType]:
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

        # create the zero-object for zero analysis (phase 2)
        zero_obj = PlanningObject("zero", "zero")

        # collect action sequences for each object
        # used for step 5: looping over consecutive transitions for an object
        obj_traces: Dict[PlanningObject, List[AP]] = defaultdict(list)
        for obs in obs_trace:
            action = obs.action
            if action is not None:
                # add the step for the zero-object
                obj_traces[zero_obj].append(AP(action, pos=0))
                # for each combination of action name A and argument pos P
                for j, obj in enumerate(action.obj_params):
                    # create transition A.P
                    ap = AP(action, pos=j + 1)  # NOTE: 1-indexed object position
                    obj_traces[obj].append(ap)

        # initialize the state set OS and transition set TS
        OS: OSType = defaultdict(list)
        TS: TSType = defaultdict(dict)
        # track pointers mapping A.P to its start and end states
        ap_state_pointers = defaultdict(dict)
        # iterate over each object and its action sequence
        for obj, seq in obj_traces.items():
            state_n = 1  # count current (new) state id
            sort = sorts[obj.name] if obj != zero_obj else 0
            TS[sort][obj] = seq  # add the sequence to the transition set
            prev_states: APStates = None  # type: ignore
            # iterate over each transition A.P in the sequence
            for ap in seq:
                # if the transition has not been seen before for the current sort
                if ap not in ap_state_pointers[sort]:
                    ap_state_pointers[sort][ap] = APStates(state_n, state_n + 1)

                    # add the start and end states to the state set as unique states
                    OS[sort].append(FSMState({state_n}))
                    OS[sort].append(FSMState({state_n + 1}))

                    state_n += 2

                ap_states = ap_state_pointers[sort][ap]

                if prev_states is not None:
                    # start = ap_states.start

                    # get the state ids (indecies) of the state sets containing
                    # start(A.P) and the end state of the previous transition
                    # start_state, prev_end_state = None, None
                    # for j, state_set in enumerate(OS[sort]):
                    #     if start in state_set:
                    #         start_state = j
                    #     if prev_states.end in state_set:
                    #         prev_end_state = j
                    #     if start_state is not None and prev_end_state is not None:
                    #         break
                    start_state, prev_end_state = LOCM._get_states(
                        OS[sort], ap_states.start, prev_states.end
                    )

                    # if not the same state set, merge the two
                    if start_state != prev_end_state:
                        OS[sort][start_state] = OS[sort][start_state].union(
                            OS[sort][prev_end_state]
                        )
                        OS[sort].pop(prev_end_state)

                prev_states = ap_states

        # remove the zero-object sort if it only has one state
        if len(OS[0]) == 1:
            ap_state_pointers[0] = {}
            OS[0] = []

        return TS, ap_state_pointers, OS

    @staticmethod
    def viz_state_machines(ap_state_pointers: APStatePointers, OS: OSType):
        from graphviz import Digraph

        state_machines = []
        for (sort, trans), states in zip(ap_state_pointers.items(), OS.values()):
            graph = Digraph(f"LOCM-phase1-sort{sort}")
            for i in range(len(states)):
                graph.node(str(i), label=f"state{i}", shape="oval")
            for ap, apstate in trans.items():
                start_idx, end_idx = LOCM._get_state(states, apstate.start, apstate.end)  # type: ignore
                graph.edge(
                    str(start_idx), str(end_idx), label=f"{ap.action.name}.{ap.pos}"
                )

            state_machines.append(graph)

        return state_machines

    @staticmethod
    def _phase3(
        TS: TSType,
        ap_state_pointers: APStatePointers,
        OS: OSType,
        sorts: Sorts,
    ):
        # 1. form hypotheses

        """
        - need the ordered transitions filtered by object from previous step
        - loop over that, for each consecutive pair check if they have a
            [not current object] param that is of the same sort
        - add [end of prior/start of latter state, parameterized by other sort, and action pair]
            - need a state obj -> ext set, store params
        """

        zero_obj = PlanningObject("zero", "zero")

        # HSIndex = NamedTuple(
        #     "HypothesisIndex", [("B", AP), ("k", int), ("C", AP), ("l", int)]
        # )

        HS: Dict[HSIndex, Set[HSItem]] = defaultdict(set)
        for G, objs in TS.items():
            for obj, seq in objs.items():
                # looping over O ∈ O_u (i.e. not including the zero-object)
                if obj == zero_obj:
                    continue
                for B, C in zip(seq, seq[1:]):
                    # FIXME: maybe bad
                    if len(B.action.obj_params) == 1 or len(C.action.obj_params) == 1:
                        continue

                    k = B.pos
                    l = C.pos
                    for i, Bk_ in enumerate(B.action.obj_params):
                        k_ = i + 1
                        if k_ == k:
                            continue
                        G_ = sorts[Bk_.name]
                        for j, Cl_ in enumerate(C.action.obj_params):
                            l_ = j + 1
                            if l_ == l:
                                continue

                            if sorts[Cl_.name] == G_:
                                S, S2 = LOCM._get_states(
                                    OS[G],
                                    ap_state_pointers[G][B].end,
                                    ap_state_pointers[G][C].start,
                                )
                                assert (
                                    S == S2
                                ), f"end(B.P) != start(C.P)\nB.P: {B}\nC.P: {C}"
                                HS[HSIndex(B, k, C, l)].add(
                                    HSItem(S, k_, l_, G, G_, supported=False)
                                )

        for G, objs in TS.items():
            for obj, seq in objs.items():
                for B, C in zip(seq, seq[1:]):
                    k = B.pos
                    l = C.pos
                    BkCl = HSIndex(B, k, C, l)
                    if BkCl in HS:
                        for H in HS[BkCl].copy():
                            if (
                                B.action.obj_params[H.k_ - 1]
                                == C.action.obj_params[H.l_ - 1]
                            ):
                                H.supported = True
                            else:
                                HS[BkCl].remove(H)

        for hs in HS.values():
            for h in hs.copy():
                if not h.supported:
                    hs.remove(h)

        for hind, hs in HS.copy().items():
            if len(hs) == 0:
                del HS[hind]

        return Hypothesis.from_dict(HS)
