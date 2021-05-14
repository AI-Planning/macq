from typing import List, Callable
import macq
from macq.trace.Fluent import CustomObject, Fluent


class Action:
    def __init__(self, name: str, obj_params: List[CustomObject], precond: List[Fluent], add: List[Fluent], 
    delete: List[Fluent], cost: int = 0):
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
        self.precond = precond
        self.add = add
        self.delete = delete
        self.cost = cost
    
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
        for fluent in fluents:
            for obj in fluent.objects:
                if obj not in self.obj_params:
                    raise InvalidFluentException()
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

class InvalidFluentException(Exception):
    def __init__(self):
        super().__init__("The fluent you want to add references objects outside of the parameters of this action.")