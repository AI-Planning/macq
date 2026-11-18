from typing import Iterable, Optional, Tuple

from ..fluents.grounded_fluent import GroundedFluent
from ..planning_object import PlanningObject
from .action_base import ActionBase


class GroundedAction(ActionBase):
    """An action applied to specific objects."""

    def __init__(
        self,
        name: str,
        objects: Iterable[PlanningObject],
        positive_preconditions: Iterable[GroundedFluent] = (),
        negative_preconditions: Iterable[GroundedFluent] = (),
        add_effects: Iterable[GroundedFluent] = (),
        delete_effects: Iterable[GroundedFluent] = (),
        cost: Optional[int] = None,
    ):
        super().__init__(name, positive_preconditions, negative_preconditions, add_effects, delete_effects)
        self._objects = tuple(objects)
        self.cost = cost

    @property
    def objects(self) -> Tuple[PlanningObject, ...]:
        return self._objects

    @property
    def signature(self) -> Tuple[str, Tuple[PlanningObject, ...]]:
        return self.name, self.objects

    def _contents(self) -> tuple:
        return super()._contents() + (self.objects, self.cost)

    def details(self) -> str:
        return f"({' '.join([self.name, *(obj.details() for obj in self.objects)])})"
