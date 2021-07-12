from collections import defaultdict
from dataclasses import dataclass
from typing import Set, List, Dict
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
    var: str

    def __hash__(self):
        return hash(self.name + " ".join(self.types))


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

        # Convert fluents to relations with instantiated objects replaced by the object type
        relations: Set[Relation] = set(
            map(
                lambda f: Relation(
                    f.name,
                    set([obj.obj_type for obj in f.objects]),
                    f"{f.name} {' '.join([obj.obj_type for obj in f.objects])}",
                ),
                fluents,
            )
        )

        action_constraints = ARMS._step2A(connected_actions, relations)
        info_constraints = ARMS._step2I(obs_lists)
        plan_constraints = ARMS._step2P(obs_lists, connected_actions, relations)

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
                    constraints.append(
                        implication(
                            f"{relation.var} in add {action.details()}",
                            f"{relation.var} notin pre {action.details()}",
                        )
                    )
                    constraints.append(
                        implication(
                            f"{relation.var} in pre {action.details()}",
                            f"{relation.var} notin add {action.details()}",
                        )
                    )

                    # A2
                    # relation in action.del => relation in action.precond
                    constraints.append(
                        implication(
                            f"{relation.var} in del {action.details()}",
                            f"{relation.var} in pre {action.details()}",
                        )
                    )

        return constraints

    @staticmethod
    def _step2I(obs_lists: ObservationLists):
        pass

    @staticmethod
    def _step2P(
        obs_lists: ObservationLists,
        connected_actions: Dict[LearnedAction, Dict[LearnedAction, Set]],
        relations: Set[Relation],
    ):
        pass
