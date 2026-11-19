from typing import List, Optional

from ..core import GroundedAction


class AtomicAction:
    """An action whose objects are given as "type name" strings.

    Atomic observation tokens use these, so that what a learner sees is plain text.
    """

    def __init__(self, name: str, obj_params: List[str], cost: Optional[int] = None):
        self.name = name
        self.obj_params = obj_params
        self.cost = cost

    @classmethod
    def of(cls, action: GroundedAction) -> "AtomicAction":
        """Returns the atomic form of a trace action."""
        return cls(action.name, [obj.details() for obj in action.objects], action.cost)

    def details(self) -> str:
        return f"{self.name} {' '.join(self.obj_params)}"

    def __repr__(self):
        return self.details()

    def __eq__(self, other):
        return (
            isinstance(other, AtomicAction)
            and self.name == other.name
            and self.obj_params == other.obj_params
        )

    def __hash__(self):
        return hash(self.details())
