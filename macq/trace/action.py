from typing import List
from .fluent import PlanningObject, Fluent


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
        precond (set):
            The set of fluents that constitute the preconditions to perform
            the action. Found during model extraction.
        add (set):
            The set of fluents that constitute the add effects of the action.
            Found during model extraction.
        delete (set):
            The set of fluents that constitute the delete effects of the
            action. Found during model extraction.
    """

    class InvalidFluent(Exception):
        def __init__(
            self,
            message="Fluent does not reference any of the objects of the action.",
        ):
            super().__init__(message)

    def __init__(
        self,
        name: str,
        obj_params: List[PlanningObject],
        cost: int = 0,
        precond: set[Fluent] = None,
        add: set[Fluent] = None,
        delete: set[Fluent] = None,
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
                The cost to perform the action.
            precond (set):
                The set of fluents that constitute the preconditions to perform
                the action.
            add (set):
                The set of fluents that constitute the add effects of the
                action.
            delete (set):
                The set of fluents that constitute the delete effects of the
                action.
        """
        self.name = name
        self.obj_params = obj_params
        self.precond = set()
        if precond is not None:
            self.update_precond(precond)
        self.add = set()
        if add is not None:
            self.update_add(add)
        self.delete = set()
        if delete is not None:
            self.update_delete(delete)
        self.cost = cost

    def __str__(self):
        string = f"{self.name} {' '.join(map(str, self.obj_params))}"
        return string

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.name == other.name and self.obj_params == other.obj_params

    def __hash__(self):
        # Order of obj_params is important!
        return hash(str(self))

    def _add_fluents(self, fluents: set[Fluent], condition: set[Fluent]):
        valid = False
        for fluent in fluents:
            for obj in fluent.objects:
                for param in self.obj_params:
                    if obj == param:
                        valid = True
                if not valid:
                    # raise self.InvalidFluent()
                    print(f'WARNING: Adding "{fluent}" as an effect of "{self.name}"')
        condition.update(fluents)

    def update_precond(self, fluents: set[Fluent]):
        """Adds preconditions to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's preconditions.
        """
        self._add_fluents(fluents, self.precond)

    def update_add(self, fluents: set[Fluent]):
        """Adds add effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's add effects.
        """
        self._add_fluents(fluents, self.add)

    def update_delete(self, fluents: set[Fluent]):
        """Adds delete effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's delete effects.
        """
        self._add_fluents(fluents, self.delete)

    def add_parameter(self, obj: PlanningObject):
        """Adds an object to the action's parameters.

        Args:
            obj (PlanningObject):
                The object to be added to the action's object parameters.
        """
        self.obj_params.append(obj)

    @classmethod
    def from_json(cls, data):
        """Converts a json object to an Action."""
        obj_params = list(map(PlanningObject.from_json, data["obj_params"]))
        precond = set(map(Fluent.from_json, data["precond"]))
        add = set(map(Fluent.from_json, data["add"]))
        delete = set(map(Fluent.from_json, data["delete"]))
        return cls(data["name"], obj_params, data["cost"], precond, add, delete)
