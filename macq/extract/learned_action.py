from __future__ import annotations
from typing import Set, List
from ..trace import Fluent


class LearnedAction:
    def __init__(self, name: str, obj_params: List[str], **kwargs):
        self.name = name
        self.obj_params = obj_params
        if "cost" in kwargs:
            self.cost = kwargs["cost"]

        self.precond = set() if "precond" not in kwargs else kwargs["precond"]
        self.add = set() if "add" not in kwargs else kwargs["add"]
        self.delete = set() if "delete" not in kwargs else kwargs["delete"]

    def __eq__(self, other):
        if not isinstance(other, LearnedAction):
            return False
        return self.name == other.name and self.obj_params == other.obj_params

    def __hash__(self):
        # Order of obj_params is important!
        return hash(self.details())

    def details(self):
        string = f"{self.name} {' '.join([o for o in self.obj_params])}"
        return string

    def update_precond(self, fluents: Set[Fluent]):
        """Adds preconditions to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's preconditions.
        """
        self.precond.update(fluents)

    def update_add(self, fluents: Set[Fluent]):
        """Adds add effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's add effects.
        """
        self.add.update(fluents)

    def update_delete(self, fluents: Set[Fluent]):
        """Adds delete effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's delete effects.
        """
        self.delete.update(fluents)

    def compare(self, orig_action: LearnedAction):
        """Compares the learned action to an original, ground truth action."""
        precond_diff = orig_action.precond.difference(self.precond)
        add_diff = orig_action.add.difference(self.add)
        delete_diff = orig_action.delete.difference(self.delete)
        return precond_diff, add_diff, delete_diff

    @classmethod
    def from_json(cls, data):
        """Converts a json object to an Action."""
        obj_params = list(map(str, data["obj_params"]))
        precond = set(map(Fluent.from_json, data["precond"]))
        add = set(map(Fluent.from_json, data["add"]))
        delete = set(map(Fluent.from_json, data["delete"]))
        return cls(
            data["name"],
            obj_params,
            cost=data["cost"],
            precond=precond,
            add=add,
            delete=delete,
        )
