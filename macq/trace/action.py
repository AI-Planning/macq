from typing import List, Set
from .fluent import Fluent, PlanningObject


class Action:
    """Grounded action.
    An Action represents a grounded action in a Trace or a Model. The action's
    `precond`, `add`, and `delete` attributes characterize a Model, and are
    found during model extraction.
    Attributes:
        name (str):
            The name of the action.
        obj_params (list):
            The list of objects the action acts on.
        cost (int):
            The cost to perform the action.
    """

    def __init__(
        self,
        name: str,
        obj_params: List[PlanningObject],
        cost: int = 0,
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
        """
        self.name = name
        self.obj_params = obj_params
        self.cost = cost

    def __str__(self):
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
        return hash(str(self))

    def update_precond(self, fluents: Set[Fluent]):
        """
        Adds the specified list of fluents to the action's preconditions.

        Args:
            fluents (set):
                The set of fluents to be added to the action's preconditions.
        """
        self.precond.update(fluents)

    def update_add(self, fluents: Set[Fluent]):
        """Adds add effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's add effects.
        """
        self.add.update(fluents)

    def update_delete(self, fluents: Set[Fluent]):
        """Adds delete effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's delete effects.
        """
        self.delete.update(fluents)

    def add_parameter(self, obj: PlanningObject):
        """Adds an object to the action's parameters.
        Args:
            obj (PlanningObject):
                The object to be added to the action's object parameters.
        """
        self.obj_params.append(obj)
