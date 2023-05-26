from typing import List, Optional, Set
from .fluent import PlanningObject, Fluent


class Action:
    """Grounded action.

    An Action represents a grounded action in a Trace or a Model. The action's
    `precond`, `add`, and `delete` attributes characterize a Model, and are
    found during model extraction.

    Attributes:
        name (str):
            The name of the action.
        obj_params (List[PlanningObject]):
            The set of objects the action acts on.
        cost (int):
            The cost to perform the action.
        precond (Set[Fluent]):
            The set of Fluents that make up the precondition.
        add (Set[Fluent]):
            The set of Fluents that make up the add effects.
        delete (Set[Fluent]):
            The set of Fluents that make up the delete effects.
    """

    def __init__(
        self,
        name: str,
        obj_params: List[PlanningObject],
        cost: int = 0,
        precond: Optional[Set[Fluent]] = None,
        add: Optional[Set[Fluent]] = None,
        delete: Optional[Set[Fluent]] = None,
    ):
        """Initializes an Action with the parameters provided.
        The `precond`, `add`, and `delete` args should only be provided in
        Model deserialization.
        Args:
            name (str):
                The name of the action.
            obj_params (list):
                The list of objects the action acts on.
            cost (int):
                Optional; The cost to perform the action. Defaults to 0.
            precond (Set[Fluent]):
                Optional; The set of Fluents that make up the precondition.
            add (Set[Fluent]):
                Optional; The set of Fluents that make up the add effects.
            delete (Set[Fluent]):
                Optional; The set of Fluents that make up the delete effects.
        """
        self.name = name
        self.obj_params = obj_params
        self.cost = cost
        self.precond = precond
        self.add = add
        self.delete = delete

    def __repr__(self):
        string = f"{self.name} {' '.join(map(str, self.obj_params))}"
        return string

    def __eq__(self, other):
        return (
            isinstance(other, Action)
            and self.name == other.name
            and self.obj_params == other.obj_params
        )

    def __hash__(self):
        # Order of obj_params is important!
        return hash(self.details())

    def details(self):
        string = f"{self.name} {' '.join([o.details() for o in self.obj_params])}"
        return string

    def clone(self, atomic=False):
        if atomic:
            return AtomicAction(
                self.name, list(map(lambda o: o.details(), self.obj_params)), self.cost
            )

        return Action(self.name, self.obj_params.copy(), self.cost)

    def _serialize(self):
        return self.name


class AtomicAction(Action):
    """An Action where the objects are represented by strings."""

    def __init__(self, name: str, obj_params: List[str], cost: int = 0):
        self.name = name
        self.obj_params = obj_params
        self.cost = cost
