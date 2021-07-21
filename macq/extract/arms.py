from collections import defaultdict, Counter
from itertools import combinations
from dataclasses import dataclass
from typing import Set, List, Dict, Tuple
from nnf import Var, And, Or
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from ..observation import PartialObservation as Observation
from ..trace import ObservationLists, Fluent, Action  # Action only used for typing


@dataclass
class Relation:
    name: str
    types: set

    def var(self):
        return f"{self.name} {' '.join(list(self.types))}"

    def __hash__(self):
        return hash(self.var())


@dataclass
class ARMSConstraints:
    action: List[Or]
    info: List[And]
    info3: Dict[Var, int]
    plan: Dict[Or, int]


class ARMS:
    """ARMS model extraction method.

    Extracts a Model from state observations using the ARMS technique. Fluents
    are retrieved from the initial state. Actions are learned using the
    algorithm.
    """

    def __new__(cls, obs_lists: ObservationLists, min_support: int = 2):
        """
        Arguments:
            obs_lists (ObservationLists):
                The observations to extract the model from.
            min_support (int):
                The minimum support count for an action pair to be considered frequent.
        """
        if obs_lists.type is not Observation:
            raise IncompatibleObservationToken(obs_lists.type, ARMS)

        # assert that there is a goal
        ARMS._check_goal(obs_lists)
        # get fluents from initial state
        fluents = ARMS._get_fluents(obs_lists)
        # call algorithm to get actions
        actions = ARMS._arms(obs_lists, fluents, min_support)
        return Model(fluents, actions)

    @staticmethod
    def _check_goal(obs_lists: ObservationLists) -> bool:
        """Checks that there is a goal state in the ObservationLists."""
        # TODO Depends on how Rebecca implements goals
        return True

    @staticmethod
    def _get_fluents(obs_lists: ObservationLists) -> Set[Fluent]:
        """Retrieves the set of fluents in the observations."""
        return obs_lists.get_fluents()

    @staticmethod
    def _arms(
        obs_lists: ObservationLists, fluents: Set[Fluent], min_support: int
    ) -> Set[LearnedAction]:
        connected_actions, learned_actions = ARMS._step1(
            obs_lists
        )  # actions = connected_actions.keys()
        constraints = ARMS._step2(
            obs_lists, connected_actions, learned_actions, fluents, min_support
        )
        max_sat = ARMS._step3(constraints)

        return set()  # WARNING temp

    @staticmethod
    def _step1(
        obs_lists: ObservationLists,
    ) -> Tuple[
        Dict[LearnedAction, Dict[LearnedAction, Set]],
        Dict[Action, LearnedAction],
    ]:
        """Substitute instantiated objects in each action instance with the object type."""

        actions: List[LearnedAction] = []
        learned_actions = {}
        for obs_action in obs_lists.get_actions():
            # We don't support objects with multiple types right now, so no
            # multiple type clauses need to be generated.

            # Create LearnedActions for each action, replacing instantiated
            # objects with the object type.
            types = {obj.obj_type for obj in obs_action.obj_params}
            action = LearnedAction(obs_action.name, types)
            actions.append(action)
            learned_actions[obs_action] = action

        connected_actions = {}
        for i, a1 in enumerate(actions):
            connected_actions[a1] = {}
            for a2 in actions[i:]:  # includes connecting with self
                intersection = a1.obj_params.intersection(a2.obj_params)
                if intersection:
                    connected_actions[a1][a2] = intersection

        return connected_actions, learned_actions

    @staticmethod
    def _step2(
        obs_lists: ObservationLists,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        learned_actions: Dict[Action, LearnedAction],
        fluents: Set[Fluent],
        min_support: int,
    ) -> ARMSConstraints:
        """Generate action constraints, information constraints, and plan constraints."""

        # Map fluents to relations
        # relations are fluents but with instantiated objects replaced by the object type
        relations: Dict[Fluent, Relation] = dict(
            map(
                lambda f: (
                    f,
                    Relation(
                        f.name,  # the fluent name
                        set([obj.obj_type for obj in f.objects]),  # the object types
                    ),
                ),
                fluents,
            )
        )

        action_constraints = ARMS._step2A(connected_actions, set(relations.values()))
        info_constraints, info_support_counts = ARMS._step2I(obs_lists, relations)
        plan_constraints = ARMS._step2P(
            obs_lists,
            connected_actions,
            learned_actions,
            set(relations.values()),
            min_support,
        )

        return ARMSConstraints(
            action_constraints, info_constraints, info_support_counts, plan_constraints
        )

    @staticmethod
    def _step2A(
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        relations: Set[Relation],
    ) -> List[Or]:
        def implication(a: Var, b: Var):
            return Or([a.negate(), b])

        constraints = []
        actions = set(connected_actions.keys())
        for action in actions:
            for relation in relations:
                # A relation is relevant to an action if they share parameter types
                if relation.types.issubset(action.obj_params):
                    # A1
                    # relation in action.add <=> relation not in action.precond

                    # _ is used to mark split locations for parsing later.
                    # Can't use spaces because both relation.var and
                    # action.details() contain spaces.
                    constraints.append(
                        implication(
                            Var(f"{relation.var()}_in_add_{action.details()}"),
                            Var(f"{relation.var()}_in_pre_{action.details()}").negate(),
                        )
                    )
                    constraints.append(
                        implication(
                            Var(f"{relation.var()}_in_pre_{action.details()}"),
                            Var(f"{relation.var()}_in_add_{action.details()}").negate(),
                        )
                    )

                    # A2
                    # relation in action.del => relation in action.precond
                    constraints.append(
                        implication(
                            Var(f"{relation.var()}_in_del_{action.details()}"),
                            Var(f"{relation.var()}_in_pre_{action.details()}"),
                        )
                    )

        return constraints

    @staticmethod
    def _step2I(
        obs_lists: ObservationLists, relations: dict
    ) -> Tuple[List[And], Dict[Var, int]]:
        constraints = []
        support_counts = defaultdict(int)
        for obs_list in obs_lists:
            for i, obs in enumerate(obs_list):
                if obs.state is not None:
                    for fluent, val in obs.state.items():
                        # Information constraints only apply to true relations
                        if val:
                            # I1
                            # relation in the add list of an action <= n (i-1)
                            i1: List[Var] = []
                            for obs_i in obs_list[: i - 1]:
                                ai = obs_i.action
                                i1.append(
                                    Var(
                                        f"{relations[fluent].var()}_in_add_{ai.details()}"
                                    )
                                )

                            # I2
                            # relation not in del list of action n (i-1)
                            i2 = Var(
                                f"{relations[fluent].var()}_in_del_{obs_list[i-1].action.details()}"
                            ).negate()

                            constraints.append(And([Or(i1), i2]))

                            # I3
                            # count occurences
                            if i < len(obs_list) - 1:
                                # corresponding constraint is related to the current action's precondition list
                                support_counts[
                                    Var(
                                        f"{relations[fluent].var()}_in_pre_{obs.action.details()}"
                                    )
                                ] += 1
                            else:
                                # corresponding constraint is related to the previous action's add list
                                support_counts[
                                    Var(
                                        f"{relations[fluent].var()}_in_add_{obs_list[i-1].action.details()}"
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
    def _step2P(
        obs_lists: ObservationLists,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        learned_actions: Dict[Action, LearnedAction],
        relations: Set[Relation],
        min_support: int,
    ) -> Dict[Or, int]:
        frequent_pairs = ARMS._apriori(
            [
                [learned_actions[obs.action] for obs in obs_list]
                for obs_list in obs_lists
            ],
            min_support,
        )

        constraints: Dict[Or, int] = {}
        for ai, aj in frequent_pairs.keys():
            # get list of relevant relations from connected_actions
            if ai in connected_actions.keys():
                relevant_relations = connected_actions[ai][aj]
            else:
                relevant_relations = connected_actions[aj][ai]

            # if the actions are not related they are not a valid pair for a plan constraint
            if not relevant_relations:
                continue

            # for each relation, save constraint
            relation_constraints = []
            for relation in relevant_relations:
                """
                ∃p(
                  (p∈ (pre_i ∩ pre_j) ∧ p∉ (del_i)) ∨
                  (p∈ (add_i ∩ pre_j)) ∨
                  (p∈ (del_i ∩ add_j))
                )
                where p is a relevant relation.
                """
                relation_constraints.append(
                    Or(
                        [
                            And(
                                [
                                    Var(f"{relation.var()}_in_pre_{ai.details()}"),
                                    Var(f"{relation.var()}_in_pre_{aj.details()}"),
                                    Var(
                                        f"{relation.var()}_in_del_{ai.details()}"
                                    ).negate(),
                                ]
                            ),
                            And(
                                [
                                    Var(f"{relation.var()}_in_add_{ai.details()}"),
                                    Var(f"{relation.var()}_in_pre_{aj.details()}"),
                                ]
                            ),
                            And(
                                [
                                    Var(f"{relation.var()}_in_del_{ai.details()}"),
                                    Var(f"{relation.var()}_in_add_{aj.details()}"),
                                ]
                            ),
                        ]
                    )
                )
            constraints[Or(relation_constraints)] = frequent_pairs[(ai, aj)]

        return constraints

    @staticmethod
    def _step3(constraints: ARMSConstraints) -> WCNF:
        # translate action constraints to pysat constraints with constant weight
        #
        pass
