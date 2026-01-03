""".. include:: ../../docs/extract/arms.md"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Hashable, List, Set, Tuple
from warnings import warn

from nnf import And, Or, Var
from nnf import false as nnffalse

from ..observation import Observation, ObservedTraceList, PartialObservation
from ..trace import Action, Fluent
from ..utils.pysat import RC2, WCNF, to_wcnf
from . import LearnedAction, LearnedFluent, Model
from .exceptions import IncompatibleObservationToken, InvalidMaxSATModel


@dataclass
class Relation:
    """Fluents with the parameters replaced by their types."""

    name: str
    types: list

    def var(self):
        """Generates the variable representation for NNF."""
        return f"{self.name} {' '.join(list(self.types))}"

    def matches(self, action: LearnedAction):
        """Determines if a relation is related to a given action."""
        action_types = set(action.obj_params)
        self_counts = Counter(self.types)
        action_counts = Counter(action.obj_params)
        return all([t in action_types for t in self.types]) and all(
            [self_counts[t] <= action_counts[t] for t in self.types]
        )

    def __hash__(self):
        return hash(self.var())


@dataclass
class ARMSConstraints:
    """A dataclass to hold all the constraints and weight information."""

    action: List[Or[Var]]
    info: List[Or[Var]]
    info3: Dict[Or[Var], int]
    plan: Dict[Or[Var], int]


class ARMS:
    """ARMS model extraction method.

    Extracts a Model from state observations using the ARMS technique. Fluents
    are retrieved from the initial state. Actions are learned using the
    algorithm.
    """

    class InvalidThreshold(Exception):
        def __init__(self, threshold):
            super().__init__(
                f"Invalid threshold value: {threshold}. Threshold must be a float between 0-1 (inclusive)."
            )

    def __new__(
        cls,
        obs_tracelist: ObservedTraceList,
        debug: bool,
        upper_bound: int,
        min_support: int = 2,
        action_weight: int = 110,
        info_weight: int = 100,
        threshold: float = 0.6,
        info3_default: int = 30,
        plan_default: int = 30,
    ):
        """
        Arguments:
            obs_tracelist (ObservationLists):
                The observations to extract the model from.
            upper_bound (int):
                The upper bound for the maximum size of an action's preconditions and
                add/delete lists. Determines when an action schemata is fully learned.
            min_support (int):
                The minimum support count for an action pair to be considered frequent.
            action_weight (int):
                The constant weight W_A(a) to assign to each action constraint.
                Should be set higher than the weight of information constraints.
            info_weight (int):
                The constant weight W_I(r) to assign to each information constraint.
                Determined empirically, generally the highest in all constraints' weights.
            threshold (float):
                (0-1). The probability threshold θ to determine if an I3/plan constraint
                is weighted by its probability or set to a default value.
            info3_default (int):
                The default weight for I3 constraints with probability below the threshold.
            plan_default (int):
                The default weight for plan constraints with probability below the threshold.
        """
        if obs_tracelist.type is not PartialObservation:
            raise IncompatibleObservationToken(obs_tracelist.type, ARMS)

        if not (threshold >= 0 and threshold <= 1):
            raise ARMS.InvalidThreshold(threshold)

        fluents = obs_tracelist.get_fluents()
        # get fluents from initial state
        # call algorithm to get actions
        actions = ARMS._arms(
            obs_tracelist,
            upper_bound,
            fluents,
            min_support,
            action_weight,
            info_weight,
            threshold,
            info3_default,
            plan_default,
            debug,
        )

        # learned_fluents = set(map(lambda f: LearnedFluent(f.name, f.objects), fluents))
        learned_fluents = set()
        # format
        for act in actions:
            act.precond = {f"({p})" for p in act.precond}
            act.add = {f"({p})" for p in act.add}
            act.delete = {f"({p})" for p in act.delete}
            learned_fluents.update(act.precond)
            learned_fluents.update(act.add)
            learned_fluents.update(act.delete)
        return Model(learned_fluents, actions)

    @staticmethod
    def _arms(
        obs_tracelist: ObservedTraceList,
        upper_bound: int,
        fluents: Set[Fluent],
        min_support: int,
        action_weight: int,
        info_weight: int,
        threshold: float,
        info3_default: int,
        plan_default: int,
        debug: bool,
    ) -> Set[LearnedAction]:
        """The main driver for the ARMS algorithm."""
        learned_actions = set()  # The set of learned action models Θ
        # pointers to the earliest unlearned action for each observation list
        early_actions = [0] * len(obs_tracelist)

        debug1 = ARMS.debug_menu("Debug step 1?") if debug else False
        connected_actions, action_map = ARMS.step1(obs_tracelist, debug1)
        if debug1:
            input("Press enter to continue...")

        action_map_rev: Dict[LearnedAction, List[Action]] = defaultdict(list)
        for obs_action, learned_action in action_map.items():
            action_map_rev[learned_action].append(obs_action)

        count = 1
        while action_map_rev:
            if debug:
                print("Iteration", count)
                count += 1

            debug2 = ARMS.debug_menu("Debug step 2?") if debug else False
            constraints, relation_map = ARMS.step2(
                obs_tracelist,
                connected_actions,
                action_map,
                fluents,
                min_support,
                debug2,
            )
            if debug2:
                input("Press enter to continue...")

            relation_map_rev: Dict[Relation, List[Fluent]] = defaultdict(list)
            for fluent, relation in relation_map.items():
                relation_map_rev[relation].append(fluent)

            debug3 = ARMS.debug_menu("Debug step 3?") if debug else False
            max_sat, decode = ARMS.step3(
                constraints,
                action_weight,
                info_weight,
                threshold,
                info3_default,
                plan_default,
                debug3,
            )
            if debug3:
                input("Press enter to continue...")

            model = ARMS.step4(max_sat, decode)

            debug5 = ARMS.debug_menu("Debug step 5?") if debug else False
            # Mutates the LearnedAction (keys) of action_map_rev
            ARMS.step5(
                model,
                list(action_map_rev.keys()),
                debug5,
            )

            # Step 5 updates

            # Progress observed states if early actions have been learned
            setA = set()
            for action in action_map_rev.keys():
                for i, obs_trace in enumerate(obs_tracelist):
                    obs_action: Action = obs_trace[early_actions[i]].action
                    # if current action is the early action for obs_trace i,
                    # update the next state with the effects and update the
                    # early action pointer
                    if obs_action in action_map and action == action_map[obs_action]:
                        print()
                        # Set add effects true
                        for add in action.add:
                            # get candidate fluents from add relation
                            # get fluent by cross referencing obs_trace.action params
                            candidates = relation_map_rev[add]
                            for fluent in candidates:
                                if set(fluent.objects).issubset(obs_action.obj_params):
                                    obs_trace[early_actions[i] + 1].state[fluent] = True
                                    early_actions[i] += 1
                        # Set del effects false
                        for delete in action.delete:
                            candidates = relation_map_rev[delete]
                            for fluent in candidates:
                                if set(fluent.objects).issubset(obs_action.obj_params):
                                    obs_trace[early_actions[i] + 1].state[
                                        fluent
                                    ] = False
                                    early_actions[i] += 1

                if debug:
                    print()
                    print(action.details())
                    print("precond:", action.precond)
                    print("add:", action.add)
                    print("delete:", action.delete)

                if (
                    max([len(action.precond), len(action.add), len(action.delete)])
                    >= upper_bound
                ):
                    if debug:
                        print(
                            f"Action schemata for {action.details()} has been fully learned."
                        )
                    setA.add(action)

            # Update Λ by Λ − A
            for action in setA:
                action_keys = action_map_rev[action]
                for obs_action in action_keys:
                    del action_map[obs_action]
                del action_map_rev[action]
                del connected_actions[action]
                action_keys = [
                    a1 for a1 in connected_actions if action in connected_actions[a1]
                ]
                for a1 in action_keys:
                    del connected_actions[a1][action]

                # Update Θ by adding A
                learned_actions.add(action)

            if debug5:
                input("Press enter to continue...")

        return learned_actions

    @staticmethod
    def step1(
        obs_tracelist: ObservedTraceList, debug: bool
    ) -> Tuple[
        Dict[LearnedAction, Dict[LearnedAction, Set[str]]],
        Dict[Action, LearnedAction],
    ]:
        """(Step 1) Substitute instantiated objects in each action instance with the object type."""

        learned_actions: Set[LearnedAction] = set()
        action_map: Dict[Action, LearnedAction] = {}
        for obs_action in obs_tracelist.get_actions():
            # We don't support objects with multiple types right now, so no
            # multiple type clauses need to be generated.

            # Create LearnedActions for each action, replacing instantiated
            # objects with the object type.
            types = [obj.obj_type for obj in obs_action.obj_params]
            learned_action = LearnedAction(obs_action.name, types)
            learned_actions.add(learned_action)
            action_map[obs_action] = learned_action

        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set[str]]] = {}
        for a1 in learned_actions:
            connected_actions[a1] = {}
            for a2 in learned_actions.difference({a1}):  # includes connecting with self
                intersection = set(a1.obj_params).intersection(set(a2.obj_params))
                if intersection:
                    connected_actions[a1][a2] = intersection
                    if debug:
                        print(
                            f"{a1.details()} is connected to {a2.details()} by {intersection}"
                        )

        return connected_actions, action_map

    @staticmethod
    def step2(
        obs_tracelist: ObservedTraceList,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set[str]]],
        action_map: Dict[Action, LearnedAction],
        fluents: Set[Fluent],
        min_support: int,
        debug: bool,
    ) -> Tuple[ARMSConstraints, Dict[Fluent, Relation]]:
        """(Step 2) Generate action constraints, information constraints, and plan constraints.

        For the unexplained actions, build a set of information and action
        constraints based on individual actions. Apply a frequent-set
        mining algorithm to find the frequent sets of connected actions and
        relations. Here connected means the actions and relations must share
        some common parameters.
        """

        # Map fluents to relations
        # relations are fluents but with instantiated objects replaced by the object type
        relations: Dict[Fluent, Relation] = dict(
            map(
                lambda f: (
                    f,
                    Relation(
                        f.name,
                        [obj.obj_type for obj in f.objects],
                    ),
                ),
                fluents,
            )
        )

        debuga = ARMS.debug_menu("Debug action constraints?") if debug else False

        action_constraints = ARMS.step2A(
            connected_actions, set(relations.values()), debuga
        )

        debugi = ARMS.debug_menu("Debug info constraints?") if debug else False
        info_constraints, info_support_counts = ARMS.step2I(
            obs_tracelist, relations, action_map, debugi
        )

        debugp = ARMS.debug_menu("Debug plan constraints?") if debug else False
        plan_constraints = ARMS.step2P(
            obs_tracelist,
            connected_actions,
            action_map,
            set(relations.values()),
            min_support,
            debugp,
        )

        return (
            ARMSConstraints(
                action_constraints,
                info_constraints,
                info_support_counts,
                plan_constraints,
            ),
            relations,
        )

    @staticmethod
    def step2A(
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        relations: Set[Relation],
        debug: bool,
    ) -> List[Or[Var]]:
        """Action constraints.

        A1. The intersection of the precondition and add lists of all actions must be empty.

        A2. In addition, if an action’s delete list includes a relation, this relation is
        in the action’s precondition list. Thus, for every action, we require that
        the delete list is a subset of the precondition list.
        """

        if debug:
            print("\nBuilding action constraints...\n")

        def implication(a: Var, b: Var):
            return Or([a.negate(), b])

        constraints: List[Or[Var]] = []
        actions = set(connected_actions.keys())
        for action in actions:
            for relation in relations:
                # A relation is relevant to an action if they share parameter types
                if relation.matches(action):
                    if debug:
                        print(
                            f'relation ({relation.var()}) is relevant to action "{action.details()}"\n'
                            "A1:\n"
                            f"  {relation.var()}∈ add ⇒ {relation.var()}∉ pre\n"
                            f"  {relation.var()}∈ pre ⇒ {relation.var()}∉ add\n"
                            "A2:\n"
                            f"  {relation.var()}∈ del ⇒ {relation.var()}∈ pre\n"
                        )

                    # A1
                    # relation in action.add => relation not in action.precond
                    # relation in action.precond => relation not in action.add

                    # (BREAK) marks unambiguous breakpoints for parsing later
                    constraints.append(
                        implication(
                            Var(
                                f"{relation.var()} (BREAK) in (BREAK) add (BREAK) {action.details()}"
                            ),
                            Var(
                                f"{relation.var()} (BREAK) in (BREAK) pre (BREAK) {action.details()}"
                            ).negate(),
                        )
                    )
                    constraints.append(
                        implication(
                            Var(
                                f"{relation.var()} (BREAK) in (BREAK) pre (BREAK) {action.details()}"
                            ),
                            Var(
                                f"{relation.var()} (BREAK) in (BREAK) add (BREAK) {action.details()}"
                            ).negate(),
                        )
                    )

                    # A2
                    # relation in action.del => relation in action.precond
                    constraints.append(
                        implication(
                            Var(
                                f"{relation.var()} (BREAK) in (BREAK) del (BREAK) {action.details()}"
                            ),
                            Var(
                                f"{relation.var()} (BREAK) in (BREAK) pre (BREAK) {action.details()}"
                            ),
                        )
                    )

        return constraints

    @staticmethod
    def step2I(
        obs_tracelist: ObservedTraceList,
        relations: Dict[Fluent, Relation],
        actions: Dict[Action, LearnedAction],
        debug: bool,
    ) -> Tuple[List[Or[Var]], Dict[Or[Var], int]]:
        """Information constraints.

        Suppose we observe a relation p to be true between two actions
        (a_n) and (a_{n+1}) , and (p, a_{i_1} , ... ,) and (a_{i_k}) share
        the same parameter types. We can represent this fact by the following clauses,
        given that (a_{i_1} , ... ,) and (a_{i_k}) appear in that order.

        I1. The relation (p) must be generated by an action (a_{i_k} (0 \le i_k \le n)),
        that is, (p) is selected to be in the add-list of (a_{i_k}).
        (p∈ (add_{i_1} ∪ add_{i_2} ∪ \dots ∪ add_{i_k}) ), where ∪ means logical “or”.

        I2. The last action (a_{i_k}) must not delete the relation p; that is,
        (p) must not be selected to be in the delete list of (a_{i_k}): (p \\not\in del_{i_k}).

        I3. We define the weight value of a relation-action pair ((p, a)) as the
        occurrence probability of this pair in all plan examples. If the probability
        of a relation-action pair is higher than the probability threshold θ ,
        then we set a corresponding relation constraint (p ∈ \\text{PRECOND}_a), which
        receives a weight value equal to its prior probability.
        """
        if debug:
            print("\nBuilding information constraints...")
        constraints: List[Or[Var]] = []
        support_counts: Dict[Or[Var], int] = defaultdict(int)
        obs_trace: List[Observation]
        for obs_trace_i, obs_trace in enumerate(obs_tracelist):
            for i, obs in enumerate(obs_trace):
                if obs.state is not None and i > 0:
                    n = i - 1
                    if debug:
                        print(
                            f"\nStep {i} of observation list {obs_trace_i} contains state information."
                        )
                    for fluent, val in obs.state.items():
                        relation = relations[fluent]
                        # Information constraints only apply to true relations
                        if val:
                            if debug:
                                print(
                                    f"  Fluent {fluent} is true.\n"
                                    f"    ({relation.var()})∈ ("
                                    f"{' ∪ '.join([f'add_{{ {actions[obs_trace[ik].action].details()} }}' for ik in range(0,n+1) if obs_trace[ik].action in actions] )}"  # type: ignore
                                    ")"
                                )
                            # I1
                            # relation in the add list of an action <= n (i-1)
                            i1: List[Var] = []
                            for obs_i in obs_trace[: i - 1]:
                                if obs_i.action in actions and obs_i.action is not None:
                                    ai = actions[obs_i.action]
                                    if relation.matches(ai):
                                        i1.append(
                                            Var(
                                                f"{relation.var()} (BREAK) in (BREAK) add (BREAK) {ai.details()}"
                                            )
                                        )

                            # I2
                            # relation not in del list of action n (i-1)
                            i2 = None
                            a_n = obs_trace[i - 1].action
                            if a_n in actions and a_n is not None:
                                i2 = Var(
                                    f"{relation.var()} (BREAK) in (BREAK) del (BREAK) {actions[a_n].details()}"
                                ).negate()

                            if i1:
                                constraints.append(Or(i1))
                            if i2:
                                constraints.append(Or([i2]))

                            # I3
                            # count occurences
                            if (
                                i < len(obs_trace) - 1
                                and obs.action in actions
                                and obs.action is not None  # for the linter
                                and relation.matches(actions[obs.action])
                            ):
                                # corresponding constraint is related to the current action's precondition list
                                support_counts[
                                    Or(
                                        [
                                            Var(
                                                f"{relation.var()} (BREAK) in (BREAK) pre (BREAK) {actions[obs.action].details()}"
                                            )
                                        ]
                                    )
                                ] += 1
                            elif (
                                a_n in actions
                                and a_n is not None
                                and relation.matches(actions[a_n])
                            ):
                                # corresponding constraint is related to the previous action's add list
                                support_counts[
                                    Or(
                                        [
                                            Var(
                                                f"{relation.var()} (BREAK) in (BREAK) add (BREAK) {actions[a_n].details()}"
                                            )
                                        ]
                                    )
                                ] += 1

        return constraints, support_counts

    @staticmethod
    def _apriori(
        action_lists: List[List[LearnedAction]], minsup: int
    ) -> Dict[Tuple[LearnedAction, LearnedAction], int]:
        """An implementation of the Apriori algorithm to find frequent ordered pairs of actions."""
        counts = Counter(
            [action for action_list in action_lists for action in action_list]
        )
        # L1 = {actions that appear >minsup}
        L1 = set(
            frozenset([action])
            for action in filter(lambda k: counts[k] >= minsup, counts.keys())
        )  # large 1-itemsets

        # Only going up to L2, so no loop or generalized algorithm needed
        # apriori-gen step
        C2 = set([i.union(j) for i in L1 for j in L1 if len(i.union(j)) == 2])
        # Since L1 contains 1-itemsets where each item is frequent, C2 can
        # only contain valid sets and pruning is not required

        # Get all possible ordered action pairs
        C2_ordered = set()
        for pair in C2:
            pair = list(pair)
            C2_ordered.add((pair[0], pair[1]))
            C2_ordered.add((pair[1], pair[0]))

        # Count pair occurences and generate L2
        frequent_pairs = {}
        for ai, aj in C2_ordered:
            count = 0
            for action_list in action_lists:
                a1_indecies = [i for i, e in enumerate(action_list) if e == ai]
                if a1_indecies:
                    for i in a1_indecies:
                        if aj in action_list[i + 1 :]:
                            count += 1
            if count >= minsup:
                frequent_pairs[(ai, aj)] = count

        return frequent_pairs

    @staticmethod
    def step2P(
        obs_tracelist: ObservedTraceList,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        action_map: Dict[Action, LearnedAction],
        relations: Set[Relation],
        min_support: int,
        debug: bool,
    ) -> Dict[Or[Var], int]:
        """Plan constraints.

        P1. Every precondition (p) of every action (b) must be in the add
        list of a preceding action (a) and is not deleted by any actions between
        (a) and (b).

        P2. In addition, at least one relation (r) in the add list of an action
        must be useful in achieving a precondition of a later action. That is, for
        every action (a), an add list relation (r) must be in the precondition of a
        later action (b), and there is no other action between (a) and (b)
        that either adds or deletes (r).

        "While constraints P1 and P2 provide the general guiding principle for
        ensuring a plan’s correctness, in practice there are too many
        instantiations of these constraints." (more information on the
        rationelle in the paper) Thus, they are replaced with the following
        constraints:

        Let there be an action pair (\langle a_i, a_j \\rangle, 0 \le i < j \le n-1).

        P3. One of the relevant relations (p) must be chosen to be in the
        preconditions of both (a_i) and (a_j), but not in the delete list
        of (a_i).

        P4. The first action (a_i) adds a relevant relation that is in the
        precondition list of the second action (a_j) in the pair.

        P5. A relevant relation (p) that is deleted by the first action
        (a_i) is added by (a_j). The second clause is designed for the event
        when an action re-establishes a fact that is deleted by a previous action.

        The above constraints can be combined into one constraint:
        $$\exists p ((p \in (pre_i \cap pre_j) \land p \\not \in (del_i)) \lor (p \in (add_i \cap pre_j)) \lor (p \in (del_i \cap add_j)))$$
        """
        frequent_pairs = ARMS._apriori(
            [
                [
                    action_map[obs.action]
                    for obs in obs_trace
                    if obs.action is not None and obs.action in action_map
                ]
                for obs_trace in obs_tracelist
            ],
            min_support,
        )
        if debug:
            print("Frequent pairs:")
            print(frequent_pairs)

        # constraints: Dict[And[Or[Var]], int] = {}
        constraints: Dict[Or[Var], int] = {}
        for ai, aj in frequent_pairs.keys():
            connectors = set()
            # get list of relevant relations from connected_actions
            if ai in connected_actions and aj in connected_actions[ai]:
                connectors.update(connected_actions[ai][aj])
            if aj in connected_actions and ai in connected_actions[aj]:
                connectors.update(connected_actions[aj][ai])

            # if the actions are not related they are not a valid pair for a plan constraint.
            if not connectors:
                continue

            # for each relation, save constraint
            relevant_relations = {p for p in relations if connectors.issubset(p.types)}
            # relation_constraints: List[Or[And[Var]]] = []
            relation_constraints: List[Var] = []
            for relation in relevant_relations:
                relation_constraints.append(
                    Var(
                        f"{relation.var()} (BREAK) relevant (BREAK) {ai.details()} (BREAK) {aj.details()}"
                    )
                )
                if debug:
                    print(
                        f"{relation.var()} might explain action pair ({ai.details()}, {aj.details()})"
                    )
            constraints[Or(relation_constraints)] = frequent_pairs[(ai, aj)]

        return constraints

    @staticmethod
    def step3(
        constraints: ARMSConstraints,
        action_weight: int,
        info_weight: int,
        threshold: float,
        info3_default: int,
        plan_default: int,
        debug: bool,
    ) -> Tuple[WCNF, Dict[int, Hashable]]:
        """(Step 3) Construct the weighted MAX-SAT problem based on the constraints and weight information found in Step 2."""

        action_weights = [action_weight] * len(constraints.action)
        info_weights = [info_weight] * len(constraints.info)
        info3_weights = ARMS._calculate_support_rates(
            list(constraints.info3.values()), threshold, info3_default
        )
        plan_weights = ARMS._calculate_support_rates(
            list(constraints.plan.values()), threshold, plan_default
        )
        all_weights = action_weights + info_weights + info3_weights + plan_weights

        info3_constraints = list(constraints.info3.keys())
        plan_constraints = list(constraints.plan.keys())
        all_constraints = (
            constraints.action + constraints.info + info3_constraints + plan_constraints
        )

        constraints_w_weights: Dict[Or[Var], int] = {}
        for constraint, weight in zip(all_constraints, all_weights):
            if constraint == nnffalse:
                continue
            if constraint not in constraints_w_weights:
                constraints_w_weights[constraint] = weight
            elif weight != constraints_w_weights[constraint]:
                if debug:
                    warn(
                        f"The constraint {constraint} has conflicting weights ({weight} and {constraints_w_weights[constraint]}). Choosing the smaller weight."
                    )
                constraints_w_weights[constraint] = min(
                    weight, constraints_w_weights[constraint]
                )

        problem: And[Or[Var]] = And(list(constraints_w_weights.keys()))
        weights = list(constraints_w_weights.values())

        wcnf, decode = to_wcnf(problem, weights)
        return wcnf, decode

    @staticmethod
    def _calculate_support_rates(
        support_counts: List[int], threshold: float, default: int
    ) -> List[int]:
        # NOTE:
        # In the paper, Z_Σ_P (denominator of the support rate formula) is
        # defined as the "total pairs" in the set of plans. However, in the
        # examples it appears that they use the max support count as the
        # denominator. My best interpretation is then to use the max support
        # count as the denominator to calculate the support rate.

        z_sigma_p = max(support_counts)

        def get_support_rate(count):
            probability = count / z_sigma_p
            return probability * 100 if probability > threshold else default

        return list(map(get_support_rate, support_counts))

    @staticmethod
    def step4(max_sat: WCNF, decode: Dict[int, Hashable]) -> Dict[Hashable, bool]:
        """(Step 4) Solve the MAX-SAT problem built in Step 3."""
        solver = RC2(max_sat)

        encoded_model = solver.compute()

        if not isinstance(encoded_model, list):
            # should never be reached
            raise InvalidMaxSATModel(encoded_model)

        # decode the model (back to nnf vars)
        model: Dict[Hashable, bool] = {
            decode[abs(clause)]: clause > 0 for clause in encoded_model
        }

        return model

    @staticmethod
    def step5(
        model: Dict[Hashable, bool],
        actions: List[LearnedAction],
        debug: bool,
    ):
        """(Step 5) Extract the learned action effects from the solved model."""
        action_map = {a.details(): a for a in actions}
        negative_constraints = defaultdict(set)
        plan_constraints: List[Tuple[str, LearnedAction, LearnedAction]] = []

        # NOTE: only taking the top n (optimal number varies, determine
        # empirically) constraints usually results in more accurate action
        # models, however this is not a part of the paper and therefore not
        # implemented.
        for constraint, val in model.items():
            constraint = str(constraint).split(" (BREAK) ")
            relation = constraint[0]
            ctype = constraint[1]  # constraint type
            if ctype == "in":
                effect = constraint[2]
                action = action_map[constraint[3]]
                if debug:
                    print(
                        f"Learned constraint: {relation} in {effect}_{action.details()}"
                    )
                if val:
                    action_update = {
                        "pre": action.update_precond,
                        "add": action.update_add,
                        "del": action.update_delete,
                    }[effect]
                    action_update({relation})
                else:
                    action_effect = {
                        "pre": action.precond,
                        "add": action.add,
                        "del": action.delete,
                    }[effect]
                    if relation in action_effect:
                        if debug:
                            warn(
                                f"Removing {relation} from {effect} of {action.details()}"
                            )
                        action_effect.remove(relation)
                    negative_constraints[(relation, action)].add(effect)

            else:  # store plan constraint
                ai = action_map[constraint[2]]
                aj = action_map[constraint[3]]
                plan_constraints.append((relation, ai, aj))
                if debug:
                    print(f"{relation} possibly explains action pair ({ai}, {aj})")

        for p, ai, aj in plan_constraints:
            if (
                not (
                    p in ai.precond.intersection(aj.precond) and p not in ai.delete
                )  # P3
                or not (p in ai.add.intersection(aj.precond))  # P4
                or not (p in ai.delete.intersection(aj.add))  # P5
            ):
                # check if either P3 or P4 are partially fulfilled and can be satisfied
                if p in ai.precond.union(aj.precond):
                    if p in aj.precond:
                        # if P3 isn't contradicted, add p to ai.precond
                        if p not in ai.delete and not (
                            (p, ai) in negative_constraints
                            and "pre" in negative_constraints[(p, ai)]
                        ):
                            ai.update_precond({p})

                        # if P4 isn't contradicted, add p to ai.add
                        if not (
                            (p, ai) in negative_constraints
                            and "add" in negative_constraints[(p, ai)]
                        ):
                            ai.update_add({p})

                    # p in ai.precond and P3 not contradicted, add p to aj.precond
                    elif p not in ai.delete and not (
                        (p, aj) in negative_constraints
                        and "pre" in negative_constraints[(p, aj)]
                    ):
                        aj.update_precond({p})

                # check if either P3 or P4 can be satisfied
                elif not (
                    (p, aj) in negative_constraints
                    and "pre" in negative_constraints[(p, aj)]
                ):
                    # if P3 isn't contradicted, add p to both ai and aj preconds
                    if p not in ai.delete and not (
                        (p, ai) in negative_constraints
                        and "pre" in negative_constraints[(p, ai)]
                    ):
                        ai.update_precond({p})
                        aj.update_precond({p})

                    # if P4 isn't contradicted, add p to ai.add and aj.precond
                    if not (
                        (p, ai) in negative_constraints
                        and "add" in negative_constraints[(p, ai)]
                    ):
                        ai.update_add({p})
                        aj.update_precond({p})

                # check if P5 can be satisfied
                # if P5 isn't contradicted, add p wherever it is missing
                if not (
                    (p, ai) in negative_constraints
                    and "del" in negative_constraints[(p, ai)]
                ) and not (
                    (p, aj) in negative_constraints
                    and "add" in negative_constraints[(p, aj)]
                ):
                    if p not in ai.delete:
                        ai.update_delete({p})
                    if p not in aj.add:
                        aj.update_add({p})

    @staticmethod
    def debug_menu(prompt: str):
        choice = input(prompt + " (y/n): ").lower()
        while choice not in ["y", "n"]:
            choice = input(prompt + " (y/n): ").lower()
        return choice == "y"
