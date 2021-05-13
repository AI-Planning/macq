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

    def add_effect(
        self,
        name: str,
        objects: List[CustomObject],
        func: Callable,
        probability: int = 100,
    ):
        """
        Creates an effect and adds it to this action.

        Arguments
        ---------
        name : str
            The name of the effect.
        objects : list
            The list of objects this effect applies to.
        func : function
            The function that applies the effect in the corresponding action.
        probability : int
            For non-deterministic problems, the probability that this effect will take place
            (defaults to 100)

        Returns
        -------
        None
        """
        for obj in objects:
            if obj not in self.obj_params:
                raise Exception(
                    "Object must be one of the objects supplied to the action"
                )
        effect = Effect(name, objects, func, probability)
        self.effects.append(effect)

    def add_precond(self, name: str, objects: List[CustomObject]):
        """
        Creates a precondition and adds it to this action.

        Arguments
        ---------
        name : str
            The name of the predicate to be used for the precondition.
        objects : list
            The list of objects this predicate applies to.

        Returns
        -------
        None
        """
        for obj in objects:
            if obj not in self.obj_params:
                raise Exception(
                    "Object must be one of the objects supplied to the action"
                )
        precond = Fluent(name, objects)
        self.precond.append(precond)

'''
class Effect(Fluent):
    def __init__(
        self,
        name: str,
        objects: List[CustomObject],
        func: Callable,
        probability: int = 100,
    ):
        """
        Class to handle an individual effect of an action.

        Arguments
        ---------
        name : str
            The name of the effect.
        objects : list
            The list of objects this effect applies to.
        func : function
            The function that applies the effect in the corresponding action.
        probability : int
            For non-deterministic problems, the probability that this effect will take place
            (defaults to 100).
        """
        super().__init__(name, objects)
        self.func = func
        self.probability = self.set_prob(probability)

    def set_prob(self, prob: int):
        """
        Setter function for probability.

        Arguments
        ---------
        prob : int
            The probability to be assigned.

        Returns
        -------
        prob : int
            The probability, after being checked for validity.
        """
        # enforce that probability is between 0 and 100 inclusive
        if prob < 0:
            prob = 0
        elif prob > 100:
            prob = 100
        return prob
'''