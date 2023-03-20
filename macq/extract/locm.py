""".. include:: ../../docs/templates/extract/locm.md"""


import itertools
from collections import defaultdict
from collections.abc import Set as SetClass
from dataclasses import asdict, dataclass
from pprint import pprint
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, Union
from warnings import warn

from macq.trace.action import Action
from macq.trace.fluent import PlanningObject

from ..observation import ActionObservation, Observation, ObservedTraceList
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .learned_fluent import LearnedFluent
from .model import Model


@dataclass
class AP:
    """Action.Position (of object parameter)"""

    action: Action
    pos: int

    def __hash__(self):
        return hash(self.action.name + str(self.pos))

    def __eq__(self, other):
        return hash(self) == hash(other)


APStates = NamedTuple("APStates", [("start", int), ("end", int)])
Sorts = Dict[str, int]  # {obj_name: sort}
APStatePointers = Dict[int, Dict[AP, APStates]]  # {sort: {AP: APStates}}


OSType = Dict[int, List[Set[int]]]  # {sort: [{states}]}
TSType = Dict[int, Dict[PlanningObject, List[AP]]]  # {sort: {obj: [AP]}}


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

    def __repr__(self) -> str:
        out = "<\n"
        for k, v in asdict(self).items():
            out += f"  {k}={v}\n"
        return out.strip() + "\n>"

    @staticmethod
    def from_dict(
        hs: Dict[HSIndex, Set[HSItem]]
    ) -> Dict[int, Dict[int, Set["Hypothesis"]]]:
        """Converts a dict of HSIndex -> HSItem to a dict of G -> S -> Hypothesis"""
        HS: Dict[int, Dict[int, Set["Hypothesis"]]] = defaultdict(
            lambda: defaultdict(set)
        )
        for hsind, hsitems in hs.items():
            hsind = hsind.__dict__
            for hsitem in hsitems:
                hsitem_dict = hsitem.__dict__
                hsitem_dict.pop("supported")
                HS[hsitem.G][hsitem.S].add(Hypothesis(**{**hsind, **hsitem_dict}))
        return HS


Hypotheses = Dict[int, Dict[int, Set[Hypothesis]]]  # {sort: {state: [Hypothesis]}}


Binding = NamedTuple("Binding", [("hypothesis", Hypothesis), ("param", int)])
Bindings = Dict[int, Dict[int, List[Binding]]]  # {sort: {state: [Binding]}}


class LOCM:
    """LOCM"""

    zero_obj = PlanningObject("zero", "zero")

    def __new__(
        cls, obs_tracelist: ObservedTraceList, statics=None, viz=False, debug=False
    ):
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

        if len(obs_tracelist) != 1:
            warn("LOCM only supports a single trace, using first trace only")

        obs_trace = obs_tracelist[0]
        fluents, actions = None, None

        sorts = LOCM._get_sorts(obs_trace, debug=debug)
        TS, ap_state_pointers, OS = LOCM._step1(obs_trace, sorts)  # includes step 2
        HS = LOCM._step3(TS, ap_state_pointers, OS, sorts)
        bindings = LOCM._step4(HS)
        bindings = LOCM._step5(HS, bindings)
        # Step 6: Extraction of static preconditions
        # Step 7: Formation of PDDL action schema

        if viz:
            state_machines = LOCM.get_state_machines(ap_state_pointers, OS, bindings)
            for sm in state_machines:
                sm.render(view=True)  # type: ignore

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
    def _pointer_to_set(states, pointer, pointer2=None) -> Tuple[int, int]:
        state1, state2 = None, None
        for i, state_set in enumerate(states):
            if pointer in state_set:
                state1 = i
            if pointer2 is None or pointer2 in state_set:
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
        """Step 1: Create a state machine for each object sort
        Implicitly includes Step 2 (zero analysis) by including the zero-object throughout
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
                    OS[sort].append({state_n})
                    OS[sort].append({state_n + 1})

                    state_n += 2

                ap_states = ap_state_pointers[sort][ap]

                if prev_states is not None:
                    # get the state ids (indecies) of the state sets containing
                    # start(A.P) and the end state of the previous transition
                    start_state, prev_end_state = LOCM._pointer_to_set(
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
    def _step3(
        TS: TSType,
        ap_state_pointers: APStatePointers,
        OS: OSType,
        sorts: Sorts,
    ) -> Hypotheses:
        """Step 3: Induction of parameterised FSMs"""

        zero_obj = LOCM.zero_obj

        # indexed by B.k and C.l for 3.2 matching hypotheses against transitions
        HS: Dict[HSIndex, Set[HSItem]] = defaultdict(set)

        # 3.1: Form hypotheses from state machines
        for G, sort_ts in TS.items():
            # for each O ∈ O_u (not including the zero-object)
            for obj, seq in sort_ts.items():
                if obj == zero_obj:
                    continue
                # for each pair of transitions B.k and C.l consecutive for O
                for B, C in zip(seq, seq[1:]):
                    # skip if B or C only have one parameter, since there is no k' or l' to match on
                    if len(B.action.obj_params) == 1 or len(C.action.obj_params) == 1:
                        continue

                    k = B.pos
                    l = C.pos

                    # check each pair B.k' and C.l'
                    for i, Bk_ in enumerate(B.action.obj_params):
                        k_ = i + 1
                        if k_ == k:
                            continue
                        G_ = sorts[Bk_.name]
                        for j, Cl_ in enumerate(C.action.obj_params):
                            l_ = j + 1
                            if l_ == l:
                                continue

                            # check that B.k' and C.l' are of the same sort
                            if sorts[Cl_.name] == G_:
                                # check that end(B.P) = start(C.P)
                                # NOTE: just a sanity check, should never fail
                                S, S2 = LOCM._pointer_to_set(
                                    OS[G],
                                    ap_state_pointers[G][B].end,
                                    ap_state_pointers[G][C].start,
                                )
                                assert (
                                    S == S2
                                ), f"end(B.P) != start(C.P)\nB.P: {B}\nC.P: {C}"

                                # save the hypothesis in the hypothesis set
                                HS[HSIndex(B, k, C, l)].add(
                                    HSItem(S, k_, l_, G, G_, supported=False)
                                )

        # 3.2: Test hypotheses against sequence
        for G, sort_ts in TS.items():
            # for each O ∈ O_u (not including the zero-object)
            for obj, seq in sort_ts.items():
                if obj == zero_obj:
                    continue
                # for each pair of transitions Ap.m and Aq.n consecutive for O
                for Ap, Aq in zip(seq, seq[1:]):
                    m = Ap.pos
                    n = Aq.pos
                    # Check if we have a hypothesis matching Ap=B, m=k, Aq=C, n=l
                    BkCl = HSIndex(Ap, m, Aq, n)
                    if BkCl in HS:
                        # check each matching hypothesis
                        for H in HS[BkCl].copy():
                            # if Op,k' = Oq,l' then mark the hypothesis as supported
                            if (
                                Ap.action.obj_params[H.k_ - 1]
                                == Aq.action.obj_params[H.l_ - 1]
                            ):
                                H.supported = True
                            else:  # otherwise remove the hypothesis
                                HS[BkCl].remove(H)

        # Remove any unsupported hypotheses (but yet undisputed)
        for hind, hs in HS.copy().items():
            for h in hs:
                if not h.supported:
                    hs.remove(h)
            if len(hs) == 0:
                del HS[hind]

        # Converts HS {HSIndex: HSItem} to a mapping of hypothesis for states of a sort {sort: {state: Hypothesis}}
        return Hypothesis.from_dict(HS)

    @staticmethod
    def _step4(HS: Dict[int, Dict[int, Set[Hypothesis]]]) -> Bindings:
        """Step 4: Creation and merging of state parameters"""

        # bindings = {sort: {state: [(hypothesis, state param)]}}
        bindings: Bindings = defaultdict(dict)
        for sort, hs_sort in HS.items():
            for state, hs_sort_state in hs_sort.items():
                # state_bindings = {hypothesis (h): state param (v)}
                state_bindings: Dict[Hypothesis, int] = {}

                # state_params = [set(v)]; params in the same set are the same
                state_params: List[Set[int]] = []

                # state_param_pointers = {v: P}; maps state param to the state_params set index
                # i.e. map hypothesis state param v -> actual state param P
                state_param_pointers: Dict[int, int] = {}

                # for each hypothesis h,
                hs_sort_state = list(hs_sort_state)
                for v, h in enumerate(hs_sort_state):
                    # add the <h, v> binding pair
                    state_bindings[h] = v
                    # add a param v as a unique state parameter
                    state_params.append({v})
                    state_param_pointers[v] = v

                # for each (unordered) pair of hypotheses h1, h2
                for i, h1 in enumerate(hs_sort_state):
                    for h2 in hs_sort_state[i + 1 :]:
                        # check if hypothesis parameters (v1 & v2) need to be unified
                        if (
                            (h1.B == h2.B and h1.k == h2.k and h1.k_ == h2.k_)
                            or
                            (h1.C == h2.C and h1.l == h2.l and h1.l_ == h2.l_)  # fmt: skip
                        ):
                            v1 = state_bindings[h1]
                            v2 = state_bindings[h2]

                            # get the parameter sets P1, P2 that v1, v2 belong to
                            P1, P2 = LOCM._pointer_to_set(state_params, v1, v2)

                            if P1 != P2:
                                # merge P1 and P2
                                state_params[P1] = state_params[P1].union(
                                    state_params[P2]
                                )
                                state_params.pop(P2)
                                state_param_pointers[v2] = P1

                # add state bindings for the sort to the output bindings
                # replacing hypothesis params with actual state params
                bindings[sort][state] = [
                    Binding(h, LOCM._pointer_to_set(state_params, v)[0])
                    for h, v in state_bindings.items()
                ]

        return bindings

    @staticmethod
    def _step5(
        HS: Dict[int, Dict[int, Set[Hypothesis]]],
        bindings: Bindings,
    ) -> Bindings:
        """Step 5: Removing parameter flaws"""

        # check each bindings[G][S] -> (h, P)
        for sort, hs_sort in HS.items():
            for state in hs_sort:
                # track all the h.Bs that occur in bindings[G][S]
                all_hB = set()
                # track the set of h.B that set parameter P
                sets_P = defaultdict(set)
                for h, P in bindings[sort][state]:
                    sets_P[P].add(h.B)
                    all_hB.add(h.B)

                # for each P, check if there is a transition h.B that never sets parameter P
                # i.e. if sets_P[P] != all_hB
                for P, setby in sets_P.items():
                    if not setby == all_hB:  # P is a flawed parameter
                        # remove all bindings referencing P
                        for h, P_ in bindings[sort][state].copy():
                            if P_ == P:
                                bindings[sort][state].remove(Binding(h, P_))
                        if len(bindings[sort][state]) == 0:
                            del bindings[sort][state]

        return bindings

    @staticmethod
    def _step7(OS: OSType, sorts: Sorts, bindings: Bindings):
        """Step 7: Formation of PDDL action schema"""
        # for each sort
        # construct a predicate for each state
        # bindings provide correlations between action params and state params
        # which occur in the start/end states of transitions

        # (:types sort1 sort2 ... sortN)
        # types = []

        # objs = {sort: [obj1, obj2, ...]}
        objs = defaultdict(list)

        """
        (:predicates 
            (s{sort}{state} ?o{sort})
            (prop{sort}{state}{prop} ?o{sort} ?p{prop})
            ...
        )
        """
        fluents = []

        # bindings = {sort: {state: [(hypothesis, state param)]}}

        for obj_name, sort in sorts.items():
            objs[sort].append(PlanningObject(f"sort{sort}", obj_name))

        print(objs)

        for sort, states in OS.items():
            for state in range(len(states)):
                for obj in objs[sort]:
                    fluent_params = [[obj]]
                    if sort in bindings and state in bindings[sort]:
                        got_params = set()
                        additional_params = []
                        for binding in bindings[sort][state]:
                            if binding.param not in got_params:
                                got_params.add(binding.param)
                                additional_params.append(binding.hypothesis.G_)
                        for param_sort in additional_params:
                            fluent_params.append(objs[param_sort])

                    # append a fluent with every combination of fluent_params
                    for params in itertools.product(*fluent_params):
                        fluents.append(
                            LearnedFluent(f"s{sort}_state{state}", list(params))
                        )

        print(fluents)
        # state_params = set()
        # for binding in bindings[sort][state]:
        # state_params.add(binding.param)

    @staticmethod
    def get_state_machines(
        ap_state_pointers: APStatePointers,
        OS: OSType,
        bindings: Optional[Bindings] = None,
    ):
        from graphviz import Digraph

        state_machines = []
        for (sort, trans), states in zip(ap_state_pointers.items(), OS.values()):
            graph = Digraph(f"LOCM-step1-sort{sort}")
            for state in range(len(states)):
                label = f"state{state}"
                if (
                    bindings is not None
                    and sort in bindings
                    and state in bindings[sort]
                ):
                    print(bindings)
                    label += f"\n["
                    params = []
                    for binding in bindings[sort][state]:
                        params.append(f"V{binding.param}")
                    label += f",".join(params)
                    label += f"]"
                graph.node(str(state), label=label, shape="oval")
            for ap, apstate in trans.items():
                start_idx, end_idx = LOCM._pointer_to_set(
                    states, apstate.start, apstate.end
                )
                graph.edge(
                    str(start_idx), str(end_idx), label=f"{ap.action.name}.{ap.pos}"
                )

            state_machines.append(graph)

        return state_machines
