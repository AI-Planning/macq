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

# step 1 types


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

# step 3 types


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
                self.G_,
            )
        )

    @staticmethod
    def from_dict(hs: Dict[HSIndex, Set[HSItem]]):
        """Converts a dict of HSIndex -> HSItem to a set of Hypothesis"""
        HS = defaultdict(lambda: defaultdict(set))
        for hsind, hsitems in hs.items():
            hsind = hsind.__dict__
            for hsitem in hsitems:
                hsitem_dict = hsitem.__dict__
                hsitem_dict.pop("supported")
                HS[hsitem.G][hsitem.S].add(Hypothesis(**{**hsind, **hsitem_dict}))
        return HS


class LOCM:
    """LOCM"""

    zero_obj = PlanningObject("zero", "zero")

    def __new__(cls, obs_tracelist: ObservedTraceList, viz=False, debug=False):
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

        sorts = LOCM._get_sorts(obs_trace, debug=debug)
        TS, ap_state_pointers, OS = LOCM._step1(obs_trace, sorts)

        if viz:
            graph = LOCM.viz_state_machines(TS, OS, sorts)
            graph.render(view=True)  # type: ignore

        return Model(fluents, actions)

    @staticmethod
    def _get_sorts(obs_trace: List[Observation], debug=False) -> Sorts:

        sorts = []  # initialize list of sorts for this trace
        # track actions seen in the trace, and the sort each actions params belong to
        ap_sort_pointers: Dict[str, List[int]] = {}
        # track objects seen in the trace, and the sort each belongs to
        # obj_sort_pointers: Dict[str, int] = {}
        sorted_objs = []

        def get_obj_sort(obj: PlanningObject) -> int:
            """Returns the sort index of the object"""
            for i, sort in enumerate(sorts):
                if obj in sort:
                    return i
            raise ValueError(f"Object {obj} not in any sort")

        for obs in obs_trace:
            action = obs.action
            if action is None:
                continue

            if debug:
                print("\n\naction:", action.name, action.obj_params)

            if action.name not in ap_sort_pointers:  # new action
                if debug:
                    print("new action")

                ap_sort_pointers[action.name] = []

                # for each parameter of the action
                for obj in action.obj_params:

                    if obj.name not in sorted_objs:  # unsorted object

                        # append a sort (set) containing the object
                        sorts.append({obj})

                        # record the object has been sorted and the index of the sort it belongs to
                        obj_sort = len(sorts) - 1
                        # obj_sort_pointers[obj.name] = obj_sort
                        sorted_objs.append(obj.name)
                        ap_sort_pointers[action.name].append(obj_sort)

                        if debug:
                            print("new object", obj.name)
                            print("sorts:", sorts)

                    else:  # object already sorted

                        # look up the sort of the object
                        obj_sort = get_obj_sort(obj)
                        ap_sort_pointers[action.name].append(obj_sort)

                        if debug:
                            print("sorted object", obj.name)
                            print("sorts:", sorts)

                if debug:
                    print("ap sorts:", ap_sort_pointers)

            else:  # action seen before
                if debug:
                    print("seen action")

                for ap_sort, obj in zip(
                    ap_sort_pointers[action.name], action.obj_params
                ):
                    if debug:
                        print("checking obj", obj.name)
                        print("ap sort:", ap_sort)

                    if obj.name not in sorted_objs:  # unsorted object
                        if debug:
                            print("unsorted object", obj.name)
                            print("sorts:", sorts)

                        # add the object to the sort of current action parameter
                        sorts[ap_sort].add(obj)
                        # obj_sort_pointers[obj.name] = ap_sort
                        sorted_objs.append(obj.name)

                    else:  # object already has a sort
                        # retrieve the sort the object belongs to
                        # obj_sort = obj_sort_pointers[obj.name]
                        obj_sort = get_obj_sort(obj)

                        if debug:
                            print(f"retrieving sorted obj {obj.name}")
                            print(f"obj_sort_idx: {obj_sort}")
                            print(f"seq_sorts: {sorts}")

                        # check if the object's sort matches the action paremeter's
                        # if so, do nothing and move on to next step
                        # otherwise, unite the two sorts
                        if obj_sort == ap_sort:
                            if debug:
                                print("obj sort matches action")
                        else:
                            if debug:
                                print(
                                    f"obj sort {obj_sort} doesn't match action {ap_sort}"
                                )
                                print(f"seq_sorts: {sorts}")

                            # unite the action parameter's sort and the object's sort
                            sorts[obj_sort] = sorts[obj_sort].union(sorts[ap_sort])

                            # drop the not unionized sort
                            sorts.pop(ap_sort)

                            old_obj_sort = obj_sort

                            obj_sort = get_obj_sort(obj)

                            if debug:
                                print(
                                    f"united seq_sorts[{ap_sort}] and seq_sorts[{obj_sort}]"
                                )
                                print(f"seq_sorts: {sorts}")
                                print(f"ap_sort_pointers: {ap_sort_pointers}")
                                print("updating pointers...")

                            min_idx = min(ap_sort, obj_sort)

                            # update all outdated records of which sort the affected objects belong to
                            for action_name, ap_sorts in ap_sort_pointers.items():
                                for p, sort in enumerate(ap_sorts):
                                    if sort == ap_sort or sort == old_obj_sort:
                                        ap_sort_pointers[action_name][p] = obj_sort
                                    elif sort > min_idx:
                                        ap_sort_pointers[action_name][p] -= 1

                            if debug:
                                print(f"ap_sort_pointers: {ap_sort_pointers}")

        obj_sorts = {}
        for i, sort in enumerate(sorts):
            for obj in sort:
                # NOTE: object sorts are 1-indexed so the zero-object can be sort 0
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
    def _step1(
        obs_trace: List[Observation], sorts: Sorts
    ) -> Tuple[TSType, APStatePointers, OSType]:
        """step 1: Create a state machine for each object sort
        Implicitly includes step 2 (zero analysis)

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

        # create the zero-object for zero analysis (step 2)
        zero_obj = LOCM.zero_obj

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
                    # get the state ids (indecies) of the state sets containing
                    # start(A.P) and the end state of the previous transition
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
            graph = Digraph(f"LOCM-step1-sort{sort}")
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
    def _step3(
        TS: TSType,
        ap_state_pointers: APStatePointers,
        OS: OSType,
        sorts: Sorts,
    ):

        zero_obj = LOCM.zero_obj
        HS: Dict[HSIndex, Set[HSItem]] = defaultdict(set)
        for G, objs in TS.items():
            for obj, seq in objs.items():
                # looping over O ∈ O_u (i.e. not including the zero-object)
                if obj == zero_obj:
                    continue
                for B, C in zip(seq, seq[1:]):
                    # skip if B or C only have one parameter, since there is no k' / l' to match on
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

    def get_param(v):
        for i, set in enum(params):
            if v in set:
                return i

    @staticmethod
    def _step4(HS: Dict[int, Dict[int, Set[Hypothesis]]]):

        bindings = defaultdict(dict)
        param_pointers = defaultdict(dict)
        params = defaultdict(dict)

        for G, hsG in HS.items():
            for S, hsS in hsG.items():
                state_bindings = {}
                state_params = []  # params to give to S
                state_param_pointers = {}

                # add a unique v
                # add a <h, vpointer> pair for each h
                hsS = list(hsS)
                for v, h in enumerate(hsS):
                    state_params.append({v})
                    state_bindings[h] = v
                    state_param_pointers[v] = v

                for i, h1 in enumerate(hsS):
                    for h2 in hsS[i + 1 :]:
                        if (
                            (h1.B == h2.B and h1.k == h2.k and h1.k_ == h2.k_)
                            or
                            (h1.C == h2.C and h1.l == h2.l and h1.l_ == h2.l_)  # fmt: skip
                        ):
                            v1 = state_bindings[h1]
                            v2 = state_bindings[h2]

                            vi1, vi2 = None, None
                            for i, param_set in enumerate(state_params):
                                if v1 in param_set:
                                    vi1 = i
                                if v2 in param_set:
                                    vi2 = i
                                if vi1 is not None and vi2 is not None:
                                    break

                            assert vi1 is not None and vi2 is not None

                            if vi1 != vi2:
                                state_params[vi1] = state_params[vi1].union(
                                    state_params[vi2]
                                )
                                state_params.pop(vi2)
                                state_param_pointers[v2] = vi1

                bindings[G][S] = state_bindings
                # {vpointer: h for h, vpointer in state_bindings.items()}
                param_pointers[G][S] = state_param_pointers
                params[G][S] = state_params

        return bindings, param_pointers, params

    @staticmethod
    def _step5(
        HS: Dict[int, Dict[int, Set[Hypothesis]]],
        bindings,
        param_pointers,
        params,
    ):
        print(list(bindings[2][1].items())[0][0])
        print("vpointer", list(bindings[2][1].items())[0][1])
        print()
        print(list(bindings[2][1].items())[1][0])
        print("vpointer", list(bindings[2][1].items())[1][1])
        print()

        for G, hsG in HS.copy().items():
            for S, hsS in hsG.copy().items():
                unique_Ps = set(param_pointers[G][S].values())
                """
                for each P (v (not pointer)) -> for index in params[G][S]
                    if there is an h in hsS that doesn't have vpointer == P
                        remove him
                """
                for P in unique_Ps:
                    for h in hsS.copy():
                        if param_pointers[G][S][bindings[G][S][h]] != P:
                            # remove P from EVERYTHING KILL IT WITH FIRE
                            pass

        return HS
