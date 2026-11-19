from .action import Action
from .state import State
from .partial_state import PartialState
from .step import Step
from .trace import Trace, SAS
from .trace_list import TraceList

# These build on macq.observation, which itself imports this package, so they load
# on first use. Importing them here would fail whenever macq.observation is imported first.
_DISORDERED = {"DisorderedParallelActionsObservationLists", "ActionPair"}


def __getattr__(name):
    if name in _DISORDERED:
        from . import disordered_parallel_actions_observation_lists as module

        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Action",
    "State",
    "PartialState",
    "Step",
    "Trace",
    "SAS",
    "TraceList",
    "DisorderedParallelActionsObservationLists",
    "ActionPair",
]
