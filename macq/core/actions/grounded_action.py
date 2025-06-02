from typing import List, Set

from ..planning_object import PlanningObject
from ..fluents.grounded_fluent import GroundedFluent


# TODO finish implementation
class GroundedAction:
    name: str
    params: List[PlanningObject]
    positive_preconditions: Set[GroundedFluent]
    negative_preconditions: Set[GroundedFluent]
    add_effects: Set[GroundedFluent]
    delete_effects: Set[GroundedFluent]
    cost: int|None


    def __init__(self, name: str, objects: List[PlanningObject],  is_strips:bool= False, cost: int=None):
        self.name =  name
        self.objects = objects
        self.is_strips = is_strips
        self.positive_preconditions = set()
        self.negative_preconditions = set()
        self.add_effects = set()
        self.delete_effects = set()
        self.cost = None

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        string = f"{self.name} {' '.join(map(str, self.obj_params))}"
        return string

    def __hash__(self):
        raise hash(self.details())

    def _serialize(self):
        return self.name

    def details(self):
        string = f"{self.name} {' '.join([o.details() for o in self.objects])}"
        return string

    def clone(self, atomic=False):
        if atomic:
            return AtomicAction(
                self.name, [obj.details() for obj in self.objects], self.cost)

        return GroundedAction(self.name, self.objects.copy(), is_strips=self.is_strips, cost=self.cost)

class AtomicAction(GroundedAction):
    """An Action where the objects are represented by strings."""

    def __init__(self, name: str, obj_params: List[str], cost: int = 0):
        super().__init__(name, [PlanningObject(obj) for obj in obj_params], cost=cost)
        self.name = name
        self.obj_params = obj_params
        self.cost = cost
