from __future__ import annotations
from typing import List, Set, Union
from . import LearnedLiftedFluent
from macq.extract.learned_fluent import ParamBoundLFluent


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
        # obj_params can be either a list of strings or a list of PlanningObject
        # depending on the token type and extraction method used to learn the action
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

    def update_precond(
            self, fluents: Union[LearnedLiftedFluent, Set[LearnedLiftedFluent], ParamBoundLFluent, Set[
                ParamBoundLFluent]]
    ):
        """Adds preconditions to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's preconditions.
        """
        if isinstance(fluents, LearnedLiftedFluent) or isinstance(fluents, ParamBoundLFluent):
            fluents = {fluents}
        self.precond.update(fluents)

    def update_add(self, fluents: Union[LearnedLiftedFluent, Set[
            LearnedLiftedFluent], ParamBoundLFluent, Set[ParamBoundLFluent]]):
        """Adds add effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's add effects.
        """
        if isinstance(fluents, LearnedLiftedFluent) or isinstance(fluents, ParamBoundLFluent):
            fluents = {fluents}
        self.add.update(fluents)

    def update_delete(
            self, fluents: Union[LearnedLiftedFluent, Set[LearnedLiftedFluent], ParamBoundLFluent, Set[
                ParamBoundLFluent]]
    ):
        """Adds delete effects to the action.

        Args:
            fluents (set):
                The set of fluents to be added to the action's delete effects.
        """
        if isinstance(fluents, LearnedLiftedFluent) or isinstance(fluents, ParamBoundLFluent):
            fluents = {fluents}
        self.delete.update(fluents)


class LiftedActionNegPrec(LearnedLiftedAction):  #TODO change class name to a more correct one
    negative_precond: Union[ParamBoundLFluent, Set[ParamBoundLFluent]]
    def __init__(self, name: str, param_sorts: List[str], **kwargs):
        super().__init__(name, param_sorts, **kwargs)
        self.negative_precond = set() if "negative_precond" not in kwargs else kwargs["negative_precond"]

    def __eq__(self, other):
        return (
                isinstance(other, LiftedActionNegPrec)
                and self.__hash__() == other.__hash__()
        )

    def __hash__(self):
        # Order of param_sorts is important!
        return hash((
             tuple(self.param_sorts),
             frozenset(self.precond),
             frozenset(self.negative_precond),
             frozenset(self.add),
             frozenset(self.delete)))

