from typing import List

from macq.trace.fluent import PlanningObject


class LearnedFluent:
    def __init__(self, name: str, objects: List[PlanningObject]):
        self.name = name
        self.objects = objects

    def __eq__(self, other):
        return isinstance(other, LearnedFluent) and hash(self) == hash(other)

    def __hash__(self):
        # Order of objects is important!
        return hash(self.details())

    def __str__(self):
        return self.details()

    def __repr__(self):
        return self.details()

    def details(self):
        # objects can be either a list of strings or a list of PlanningObject depending on the token type and extraction method used to learn the fluent
        if len(self.objects) > 0:
            try:
                string = f"{self.name} {' '.join([o for o in self.objects])}"
            except TypeError:
                string = f"{self.name} {' '.join([o.details() for o in self.objects])}"
        else:
            string = self.name
        return f"({string})"

    def _serialize(self):
        return str(self)


class LearnedLiftedFluent:
    def __init__(self, name: str, param_sorts: List[str], param_act_inds: List[int]):
        self.name = name
        self.param_sorts = param_sorts
        self.param_act_inds = param_act_inds

    def __eq__(self, other):
        return isinstance(other, LearnedLiftedFluent) and hash(self) == hash(other)

    def __hash__(self):
        # Order of objects is important!
        return hash(self.details())

    def __str__(self):
        return self.details() + f" {self.param_act_inds}"

    def __repr__(self):
        return self.details()

    def details(self):
        return f"({self.name} {' '.join(self.param_sorts)})"

    def _serialize(self):
        return str(self)


class ParamBoundLFluent:
    """
    solves the problem for some extraction methods that requires differences between param_act_inds for sorting
    """

    def __init__(self, name: str, param_sorts: List[str], param_act_inds: List[int]):
        self.name = name
        self.param_sorts = param_sorts
        self.param_act_inds = param_act_inds

    def __eq__(self, other):
        return isinstance(other, ParamBoundLFluent) and hash(self) == hash(other)

    def __hash__(self):
        # Order of objects is important!
        return hash(f"({self.name} {' '.join(self.param_sorts)} {' '.join(map(str, self.param_act_inds))})")

    def __str__(self):
        return self.details() + f" {self.param_act_inds}"

    def __repr__(self):
        return self.details()

    def details(self):
        return f"({self.name} {' '.join(self.param_sorts)} )"

    def _serialize(self):
        return str(self)

    def to_LearnedLiftedFluent(self) -> LearnedLiftedFluent:
        return LearnedLiftedFluent(self.name, self.param_sorts, self.param_act_inds)
