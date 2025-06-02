from __future__ import annotations

from typing import List, Set, Union

from . import LearnedLiftedFluent


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
        return (
            isinstance(other, LearnedAction)
            and self.name == other.name
            and self.obj_params == other.obj_params
        )

    def __hash__(self):
        # Order of obj_params is important!
        return hash(self.details())

    def details(self):
        # obj_params can be either a list of strings or a list of PlanningObject depending on the token type and extraction method used to learn the action
        try:
            string = f"({self.name} {' '.join(self.obj_params)})"
        except TypeError:
            string = f"({self.name} {' '.join([o.details() for o in self.obj_params])})"

        return string

    def update_precond(self, fluents: Set[str]):
        """Adds preconditions to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's preconditions.
        """
        self.precond.update(fluents)

    def update_add(self, fluents: Set[str]):
        """Adds add effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's add effects.
        """
        self.add.update(fluents)

    def update_delete(self, fluents: Set[str]):
        """Adds delete effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's delete effects.
        """
        self.delete.update(fluents)

    def clear(self):
        self.precond = set()
        self.add = set()
        self.delete = set()

    def compare(self, orig_action: LearnedAction):
        """Compares the learned action to an original, ground truth action."""
        precond_diff = orig_action.precond.difference(self.precond)
        add_diff = orig_action.add.difference(self.add)
        delete_diff = orig_action.delete.difference(self.delete)
        return precond_diff, add_diff, delete_diff

    def _serialize(self):
        return dict(
            name=self.name,
            obj_params=self.obj_params,
            cost=self.cost,
            precond=list(self.precond),
            add=list(self.add),
            delete=list(self.delete),
        )

    @classmethod
    def _deserialize(cls, data):
        """Converts a json object to an Action."""
        precond = set(data["precond"])
        add = set(data["add"])
        delete = set(data["delete"])
        return cls(
            data["name"],
            data["obj_params"],
            cost=data["cost"],
            precond=precond,
            add=add,
            delete=delete,
        )


class LearnedLiftedAction:
    def __init__(self, name: str, param_sorts: List[str], **kwargs):
        self.name = name
        self.param_sorts = param_sorts
        self.precond = set() if "precond" not in kwargs else kwargs["precond"]
        self.add = set() if "add" not in kwargs else kwargs["add"]
        self.delete = set() if "delete" not in kwargs else kwargs["delete"]

    def __eq__(self, other):
        return (
            isinstance(other, LearnedLiftedAction)
            and self.name == other.name
            and self.param_sorts == other.param_sorts
        )

    def __hash__(self):
        # Order of param_sorts is important!
        return hash(self.details())

    def __repr__(self) -> str:
        return self.details()

    def details(self):
        return f"({self.name} {' '.join(self.param_sorts)})"

    # NOTE that by definition the preconditions of
    # a lifted action is a set of parameter-bound-literals and not a lifted fluent
    # the LearnedLiftedFluent is in fact implemented as a partially parameter-bound literal and partially lifted fluent.
    # notice the hash function if the class referring to the object as a lifted fluent, whereas the constructor refers to
    # the object as a parameter-bound literal by initializing the param-act_inds field. that causes a hash collision when implementing learning
    # algorithms and referring the set as a parameter-bound literal. I would suggest renaming classes and fixing classes definitions to fit the mathematical definitions.
    def update_precond(
        self, fluents: Union[LearnedLiftedFluent, Set[LearnedLiftedFluent]]
    ):
        """Adds preconditions to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's preconditions.
        """
        if isinstance(fluents, LearnedLiftedFluent):
            fluents = {fluents}
        self.precond.update(fluents)

    def update_add(self, fluents: Union[LearnedLiftedFluent, Set[LearnedLiftedFluent]]):
        """Adds add effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's add effects.
        """
        if isinstance(fluents, LearnedLiftedFluent):
            fluents = {fluents}
        self.add.update(fluents)

    def update_delete(
        self, fluents: Union[LearnedLiftedFluent, Set[LearnedLiftedFluent]]
    ):
        """Adds delete effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's delete effects.
        """
        if isinstance(fluents, LearnedLiftedFluent):
            fluents = {fluents}
        self.delete.update(fluents)
