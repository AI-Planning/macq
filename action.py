from predicate import Predicate
from effect import Effect
from collections.abc import Callable, Sequence

class Action:
    def __init__(self, name, obj_params):
        """Class to handle each action"""
        # name of the action
        self.name = name
        # assign objects it is applied to
        self.obj_params = obj_params
        # preconditions for the action
        self.precond = []
        # effects for the action
        self.effects = []

    def add_effect(self, name, objects, func, probability=100):
        """Creates an effect and adds it to this action"""
        for obj in objects:
            if obj not in self.obj_params:
               raise Exception("Object must be one of the objects supplied to the action")
        effect = Effect(name, objects, func, probability=100)
        self.effects.append(effect)

    def add_precond(self, name, objects):
        """Creates a precondition and adds it to this action"""
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
