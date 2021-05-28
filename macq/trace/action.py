from typing import List
from .fluent import PlanningObject, Fluent


class Action:
    class InvalidFluent(Exception):
        """
        The Exception raised when the user attempts to add fluents (to a precondition or effect) that act on objects
        outside of the parameters supplied to the action.
        """

        def __init__(
            self,
            message="Cannot add a fluent referencing objects beyond the scope of this action.",
        ):
            super().__init__(message)

    def __init__(
        self,
        name: str,
        obj_params: List[PlanningObject],
        precond: set[Fluent] = None,
        add: set[Fluent] = None,
        delete: set[Fluent] = None,
        cost: int = 0,
    ):
        """
        Class to handle each action.

        Arguments
        ---------
        name : str
            The name of the action.
        obj_params : list
            The list of objects this action can apply to.
        precond: list of Fluents
            The list of preconditions that must pass before this action takes place.
        add : list of Fluents
            The list of fluents to be flipped to True after this action takes place.
        delete : list of Fluents
            The list of fluents to be flipped to False after this action takes place.
        cost : int
            The cost of this action.
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
        string = f"{self.name}"
        return string

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.name == other.name and self.obj_params == other.obj_params

    def __hash__(self):
        return hash(str(self))

    def __add_fluents(self, fluents: set[Fluent], condition: set[Fluent]):
        """
        Checks the validity of a fluent before adding it to either the action's preconditions,
        add effects or delete effects.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the given action condition.
        condition : list of Fluents
            Either the action's preconditions, add effects, or delete effects to be added to.
        """
        for fluent in fluents:
            for obj in fluent.objects:
                if obj not in self.obj_params:
                    raise self.InvalidFluent()
        condition.update(fluents)

    def update_precond(self, fluents: set[Fluent]):
        """
        Adds the specified list of fluents to the action's preconditions.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the action's preconditions.
        """
        self.__add_fluents(fluents, self.precond)

    def update_add(self, fluents: set[Fluent]):
        """
        Adds the specified list of fluents to the action's add effects.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the action's add effects.
        """
        self.__add_fluents(fluents, self.add)

    def update_delete(self, fluents: set[Fluent]):
        """
        Adds the specified list of fluents to the action's delete effects.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the action's delete effects.
        """
        self.__add_fluents(fluents, self.delete)

    def add_parameter(self, obj: PlanningObject):
        """
        Adds the specified object to the action's list of available parameters.

        Arguments
        ---------
        obj : CustomObject
            The object to be added to the action's list of available parameters.
        """
        self.obj_params.append(obj)

    def copy(self):
        name = self.name
        obj_params = self.obj_params.copy()
        precond = self.precond.copy()
        add = self.add.copy()
        delete = self.delete.copy()
        cost = self.cost
        return Action(name, obj_params, precond, add, delete, cost)

    @classmethod
    def from_json(cls, data):
        """
        Converts a json object to an Action object.

        Arguments
        ---------
        data : dict
            The json object.

        Returns
        -------
        The corresponding Action object : Action
        """
        obj_params = list(map(PlanningObject.from_json, data["obj_params"]))
        precond = list(map(Fluent.from_json, data["precond"]))
        add = list(map(Fluent.from_json, data["add"]))
        delete = list(map(Fluent.from_json, data["delete"]))
        return cls(data["name"], obj_params, precond, add, delete, data["cost"])
