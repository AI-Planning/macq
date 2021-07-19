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
from ..trace import ObservationLists, Fluent


@dataclass
class Relation:
    name: str
    types: set

    def var(self):
        return f"{self.name} {' '.join(list(self.types))}"

    def __hash__(self):
        return hash(self.var())


class ARMS:
    """ARMS model extraction method.

    Extracts a Model from state observations using the ARMS technique. Fluents
    are retrieved from the initial state. Actions are learned using the
    algorithm.
    """

    def __new__(cls, obs_lists: ObservationLists):
        if obs_lists.type is not Observation:
            raise IncompatibleObservationToken(obs_lists.type, ARMS)

        # assert that there is a goal
        ARMS._check_goal(obs_lists)
        # get fluents from initial state
        fluents = ARMS._get_fluents(obs_lists)
        # call algorithm to get actions
        actions = ARMS._arms(obs_lists, fluents)
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
    def _arms(obs_lists: ObservationLists, fluents: Set[Fluent]) -> Set[LearnedAction]:
        connected_actions = ARMS._step1(obs_lists)  # actions = connected_actions.keys()
        constraints = ARMS._step2(obs_lists, connected_actions, fluents)

        return set()  # WARNING temp

    @staticmethod
    def _step1(
        obs_lists: ObservationLists,
    ) -> Dict[LearnedAction, Dict[LearnedAction, Set]]:
        """Substitute instantiated objects in each action instance with the object type."""

        actions: List[LearnedAction] = []
        for obs_action in obs_lists.get_actions():
            # We don't support objects with multiple types right now, so no
            # multiple type clauses need to be generated.

            # Create LearnedActions for each action, replacing instantiated
            # objects with the object type.
            types = {obj.obj_type for obj in obs_action.obj_params}
            action = LearnedAction(obs_action.name, types)
            actions.append(action)

        connected_actions = {}
        for i, a1 in enumerate(actions):
            connected_actions[a1] = {}
            for a2 in actions[i:]:  # includes connecting with self
                intersection = a1.obj_params.intersection(a2.obj_params)
                if intersection:
                    connected_actions[a1][a2] = intersection

        return connected_actions

    @staticmethod
    def _step2(
        obs_lists: ObservationLists,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        fluents: Set[Fluent],
    ) -> List:
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
        info_constraints, support_counts = ARMS._step2I(obs_lists, relations)
        """
        # calculate support rates
        support_rate = {}

        # NOTE:
        # In the paper, Z_Σ_P (denominator of the support rate formula) is
        # defined as the "total pairs" in the set of plans. However, in the
        # examples it appears that they use the max support count as the
        # denominator. My best interpretation is then to use the max support
        # count as the denominator to calculate the support rate.
        z_sigma_p = max(support_counts.values())
        for pair, support_count in support_counts.items():
            support_rate[pair] = support_count / z_sigma_p

            # weight of (p,a) is the occurence probability
            # if probability > theta, p in pre of a, with weight =
            # prior probability
        """
        # plan_constraints = ARMS._step2P(obs_lists, connected_actions, relations)

        return []  # WARNING temp

    @staticmethod
    def _step2A(
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        relations: Set[Relation],
    ):
        def implication(a: str, b: str):
            return Or([Var(a).negate(), Var(b)])

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
                            f"{relation.var()}_in_add_{action.details()}",
                            f"{relation.var()}_notin_pre_{action.details()}",
                        )
                    )
                    constraints.append(
                        implication(
                            f"{relation.var()}_in_pre_{action.details()}",
                            f"{relation.var()}_notin_add_{action.details()}",
                        )
                    )

                    # A2
                    # relation in action.del => relation in action.precond
                    constraints.append(
                        implication(
                            f"{relation.var()}_in_del_{action.details()}",
                            f"{relation.var()}_in_pre_{action.details()}",
                        )
                    )

        return constraints

    @staticmethod
    def _step2I(obs_lists: ObservationLists, relations: dict):
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
                            for obs_i in obs_list[:i]:
                                a_i = obs_i.action
                                i1.append(
                                    Var(
                                        f"{relations[fluent].var()}_in_add_{a_i.details()}"
                                    )
                                )

                            # I2
                            # relation not in del list of action n (i-1)
                            i2 = Var(
                                f"{relations[fluent].var()}_notin_del_{obs_list[i-1].action.details()}"
                            )

                            constraints.append(And([Or(i1), i2]))

                            # I3
                            # count occurences
                            if i < len(obs_list) - 1:
                                # corresponding constraint is related to the current action's precondition list
                                support_counts[
                                    (relations[fluent], obs.action, "pre")
                                ] += 1
                            else:
                                # corresponding constraint is related to the previous action's add list
                                support_counts[
                                    (relations[fluent], obs_list[i - 1].action, "add")
                                ] += 1

        return constraints, support_counts

    @staticmethod
    def apriori(action_lists, minsup) -> Set[Tuple[LearnedAction]]:
        counts = Counter(
            [action for action_list in action_lists for action in action_list]
        )
        # L1 = {actions that appear >minsup}
        L1 = set(
            frozenset(action)
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
        L2 = set()
        for a1, a2 in C2_ordered:
            count = 0
            for action_list in action_lists:
                a1_indecies = [i for i, e in enumerate(action_list) if e == a1]
                if a1_indecies:
                    for i in a1_indecies:
                        if a2 in action_list[i + 1 :]:
                            count += 1
            if count >= minsup:
                L2.add((a1, a2))

        return L2

    @staticmethod
    def _step2P(
        obs_lists: ObservationLists,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        relations: Set[Relation],
    ):
        frequent_pairs = ARMS.apriori(
            [[obs.action for obs in obs_list] for obs_list in obs_lists]
        )
