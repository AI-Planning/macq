from ..trace import Step, Fluent
from . import NoisyPartialObservation
from typing import Set


class NoisyPartialDisorderedParallelObservation(NoisyPartialObservation):
    """The Noisy Partial Observability Token, with possibly Disordered and Parallel Actions.

    The noisy partial observability token with disordered and parallel actions stores the step where some of the values of
    the fluents in the step's state are incorrect (noisy) or unknown (partial). In addition, the action stored also may or may not be
    disordered with an action in another parallel action set. Finally, a "parallel action set ID" is stored which indicates
    which parallel action set the token is a part of. Inherits the NoisyPartialObservation token class.
    """

    def __init__(
        self,
        step: Step,
        par_act_set_ID: int,
        percent_missing: float = 0,
        hide: Set[Fluent] = None,
        percent_noisy: float = 0,
        replace: bool = False,
    ):
        """
        Creates an NoisyPartialDisorderedParallelObservation object.

        Args:
            step (Step):
                The step associated with this observation.
            par_act_set_ID (int):
                The ID that identifies which parallel action set the action in this step is a part of.
            percent_missing (float):
                The percentage of fluents to randomly hide in the observation.
            hide (Set[Fluent]):
                The set of fluents to explicitly hide in the observation.
            percent_noisy (float):
                The percentage of fluents to randomly make noisy in the observation.
            replace (bool):
                Option to replace noisy fluents with the values of other existing fluents instead
                of just flipping their values.
        """
        super().__init__(
            step=step,
            percent_missing=percent_missing,
            hide=hide,
            percent_noisy=percent_noisy,
            replace=replace,
        )
        self.par_act_set_ID = par_act_set_ID
