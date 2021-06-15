from . import PartialObservabilityToken
from typing import Callable, Union, Set
from ..trace import Step, Fluent
import nnf


class PartialObservabilityTokenPropositions(PartialObservabilityToken):
    def __init__(
        self,
        step: Step,
        method: Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs
    ):
        super().__init__(step, method, **method_kwargs)
        self.step = self.convert_to_propositions()

    def convert_to_propositions(self):
        formula = None
        for fluent in self.step.state:
            next = nnf.Var(fluent.details())
            if formula:
                formula = formula & next
            else:
                formula = next
        return formula
