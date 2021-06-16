from . import PartialObservabilityToken
from typing import Callable, Union, Set
from ..trace import Step, Fluent
from nnf import Var


class PartialObservabilityTokenPropositions(PartialObservabilityToken):
    def __init__(
        self,
        step: Step,
        method: Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs
    ):
        super().__init__(step, method, **method_kwargs)
        self.step.state = self.convert_to_propositions()

    def convert_to_propositions(self):
        formula = None
        state = self.step.state
        for fluent in state:
            next = Var(fluent.details())
            if not state[fluent]:
                next = ~next
            if formula:
                formula = (formula & next).simplify()
            else:
                formula = next
        return formula

    def get_base_fluents(self):
        fluents = set()
        fluents.update(f if f.true else ~f for f in self.step.state.children)
        return fluents
