from predicate import Predicate
from effect import Effect
from collections.abc import Callable, Sequence

class Action:
    def __init__(self, name, obj_params):
        """
        Class to handle each action.

        Arguments
        ---------
        name : string
            The name of the action.
        obj_params : list
            The list of objects this action applies to.

        Other Class Attributes
        ---------
        precond : list of Predicates
            The list of preconditions needed for this action.
        effects : list of Effects
            The list of effects this action results in/
        """
        self.name = name
        self.obj_params = obj_params
        self.precond = []
        self.effects = []

    def add_effect(self, name, objects, func, probability=100):
        """
        Creates an effect and adds it to this action.

        Arguments
        ---------
        name : string
            The name of the effect.
        objects : list 
            The list of objects this effect applies to.
        func : string
            The name of the function that applies the effect in the corresponding action.
        probability : int
            For non-deterministic problems, the probability that this effect will take place
            (defaults to 100)

        Returns
        -------
        None
        """
        for obj in objects:
            if obj not in self.obj_params:
               raise Exception("Object must be one of the objects supplied to the action")
        effect = Effect(name, objects, func, probability=100)
        self.effects.append(effect)

    def add_precond(self, name, objects):
        """
        Creates a precondition and adds it to this action.

        Arguments
        ---------
        name : string
            The name of the predicate to be used for the precondition.
        objects : list
            The list of objects this predicate applies to.

        Returns
        -------
        None
        """
        for obj in objects:
            if obj not in self.obj_params:
                raise Exception("Object must be one of the objects supplied to the action")
        precond = Predicate(name, objects)
        self.precond.append(precond)
    

if __name__ == "__main__":
    action = Action("put down", ["block 1", "block 2"])
    action.add_effect("eff", ["block 1", "block 2"], "func1", 94)
    action.add_precond("precond", ["block 1", "block 2"])
    action.add_effect("eff", ["block 1", "block 3"], "func1", 94)
