from typing import List, Set

from ..signature_parameter import SignatureParameter
from ..fluents.parameter_bound_fluent import ParameterBoundFluent

class LiftedAction:

    name: str
    params: List[SignatureParameter]
    positive_preconditions: Set[ParameterBoundFluent]
    negative_preconditions: Set[ParameterBoundFluent] | None
    add_effects: Set[ParameterBoundFluent]
    delete_effects: Set[ParameterBoundFluent]


    def __init__(self, name: str, params: List[SignatureParameter]):
        self.positive_preconditions = set()
        self.negative_preconditions = None
        self.add_effects = set()
        self.delete_effects = set()
        self.name = name
        self.params = params


    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((
             self.name,
             tuple(self.params),
             frozenset(self.positive_preconditions),
             frozenset(self.negative_preconditions),
             frozenset(self.add_effects),
             frozenset(self.delete_effects),))


    def __str__(self):
        return self.details()

    def details(self):
        return f"({self.name} {' '.join(param.object_type.type_name for param in self.params)})"

    def __repr__(self) -> str:
        return self.details()
