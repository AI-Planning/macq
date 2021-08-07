from ..trace import Step, Fluent, State
from . import NoisyPartialObservation
from typing import Set
import random


class NoisyPartialDisorderedParallelObservation(NoisyPartialObservation):
    def __init__(self, step: Step, percent_missing: float = 0, hide: Set[Fluent] = None, percent_noisy: float = 0):

        super().__init__(step=step, percent_missing=percent_missing, hide=hide, percent_noisy=percent_noisy)
