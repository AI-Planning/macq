from typing import List
from .fluent import CustomObject, Fluent


class Action:
    class InvalidFluent(Exception):
        """
        Raised when the user attempts to add fluents (to a precondition or effect) that act on objects
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
        obj_params: List[CustomObject],
        precond: List[Fluent],
        add: List[Fluent],
        delete: List[Fluent],
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
        self.precond = []
        self.add_precond(precond)
        self.add = []
        self.add_effect_add(add)
        self.delete = []
        self.add_effect_delete(delete)
        self.cost = cost

    def __repr__(self):
        string = "Action with Name: " + self.name + "\n\nObject Parameters:\n"
        for obj in self.obj_params:
            string += str(obj) + "\n"
        string += "\nPreconditions:\n"
        for fluent in self.precond:
            string += str(fluent) + "\n\n"
        string += "\nEffects to add:\n"
        for fluent in self.add:
            string += str(fluent) + "\n\n"
        string += "\nEffects to delete:\n"
        for fluent in self.delete:
            string += str(fluent) + "\n\n"
        string += "\nCost: " + str(self.cost)
        return string

    def __add_fluent(self, fluents: List[Fluent], condition: List[Fluent]):
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
        valid = False
        for fluent in fluents:
            for obj in fluent.objects:
                # if this fluent takes no parameters it is automatically valid
                if (
                    len(fluent.objects) == 1
                    and fluent.objects[0].name == ""
                    and fluent.objects[0].obj_type == ""
                ):
                    valid = True
                else:
                    for param in self.obj_params:
                        if obj == param:
                            valid = True
                            # no need to check the rest
                            break
                if not valid:
                    raise self.InvalidFluent()
                # reset flag
                valid = False
        condition.extend(fluents)

    def add_precond(self, fluents: List[Fluent]):
        """
        Adds the specified list of fluents to the action's preconditions.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the action's preconditions.
        """
        self.__add_fluent(fluents, self.precond)

    def add_effect_add(self, fluents: List[Fluent]):
        """
        Adds the specified list of fluents to the action's add effects.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the action's add effects.
        """
        self.__add_fluent(fluents, self.add)

    def add_effect_delete(self, fluents: List[Fluent]):
        """
        Adds the specified list of fluents to the action's delete effects.

        Arguments
        ---------
        fluents : list of Fluents
            The list of fluents to be added to the action's delete effects.
        """
        self.__add_fluent(fluents, self.delete)

    def add_parameter(self, obj: CustomObject):
        """
        Adds the specified object to the action's list of available parameters.

        Arguments
        ---------
        obj : CustomObject
            The object to be added to the action's list of available parameters.
        """
        self.obj_params.append(obj)
