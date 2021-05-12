from predicate import Predicate
from effect import Effect
from collections.abc import Callable, Sequence

class Action:
    def __init__(self, name, obj_params, precond: Union[Predicate, Sequence[Predicate]], effects: 
        [Effect, Sequence[Effect]]):
        """Class to handle each action"""
        # name of the action
        self.name = name
        # assign objects it is applied to
        self.obj_params = obj_params
        # preconditions for the action
        self.precond = precond
        # effects for the action
        self.effects = effects

eff = Effect("eff", ["block 1", "block 2"], "func1", 94)
precond = Predicate("pred1", ["block A", "block B"])
action = ("put down", [""])