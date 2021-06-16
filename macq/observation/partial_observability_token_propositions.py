from . import PartialObservabilityToken
from typing import Callable, Union, Set
from ..trace import Step, Fluent
import bauhaus
from bauhaus import Encoding, proposition


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
        e = Encoding()

        @proposition(e)
        class fluent(object):
            # instantiate with name to be given to the proposition
            def __init__(self, name):
                self.name = name

        state = self.step.state
        for f in state:
            next = fluent(f.details())
            if state[f]:
                e.add_constraint(next)
            else:
                e.add_constraint(~next)
        return e
