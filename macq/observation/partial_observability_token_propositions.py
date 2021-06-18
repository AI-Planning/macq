from . import PartialObservabilityToken
from ..trace import Step, Fluent
from typing import Callable, Union, Set
from bauhaus import Encoding, proposition
from bauhaus.core import CustomNNF

# e = Encoding()


class PartialObservabilityTokenPropositions(PartialObservabilityToken):
    def __init__(
        self,
        step: Step,
        method: Union[Callable[[int], Step], Callable[[Set[Fluent]], Step]],
        **method_kwargs
    ):
        super().__init__(step, method, **method_kwargs)
        # self.step.state = self.convert_to_encoding()

    """
    def convert_to_encoding(self):
        global e
        state = self.step.state
        for f in state:
            next = fluent(f.details()) 
            if not state[f]:
                next = ~next
            e.add_constraint(next)
        return e
    """

    def get_base_true_fluents(self):
        fluents = set()
        """
        #fluents.update(f if not f._var.true else ~f for f in self.step.state._custom_constraints)
        for f in self.step.state._custom_constraints:
            if isinstance(f, CustomNNF):
                fluents.update([f if f.typ != "not" else ~f])
            else:
                fluents.update([f if f._var.true else ~f])
        return fluents
        """
        for f in self.step.state.fluents:
            fluents.add(f.details())
        return fluents
