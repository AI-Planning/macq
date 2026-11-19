from typing import Iterable, Tuple

from ..fluents.parameter_bound_fluent import ParameterBoundFluent
from ..object_type import ObjectType
from ..signature_parameter import SignatureParameter
from .action_base import ActionBase


class LiftedAction(ActionBase):
    """An action stated over typed parameters, with fluents bound to those parameters."""

    def __init__(
        self,
        name: str,
        params: Iterable[SignatureParameter],
        positive_preconditions: Iterable[ParameterBoundFluent] = (),
        negative_preconditions: Iterable[ParameterBoundFluent] = (),
        add_effects: Iterable[ParameterBoundFluent] = (),
        delete_effects: Iterable[ParameterBoundFluent] = (),
    ):
        super().__init__(name, positive_preconditions, negative_preconditions, add_effects, delete_effects)
        self._params = tuple(params)

    @property
    def params(self) -> Tuple[SignatureParameter, ...]:
        return self._params

    @property
    def signature(self) -> Tuple[str, Tuple[ObjectType, ...]]:
        return self.name, tuple(param.object_type for param in self.params)

    def _contents(self) -> tuple:
        return super()._contents() + (self.params,)

    def details(self) -> str:
        return f"({' '.join([self.name, *(param.details() for param in self.params)])})"
