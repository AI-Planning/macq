from enum import Enum, auto
from .model import Model
from ..trace import TraceList, State


class modes(Enum):
    OBSERVER = auto()


class Extract:
    def __new__(cls, traces: TraceList, mode: modes):
        if mode == modes.OBSERVER:
            return Extract._extract_observer(traces)

    @staticmethod
    def _get_fluents(traces: TraceList):
        fluents = set()
        for trace in traces:
            for fluent in trace.fluents:
                fluents.add(fluent)
        return list(fluents)

    @staticmethod
    def _get_actions(traces: TraceList):
        actions = set()
        for trace in traces:
            for action in trace.actions:
                actions.add(action)
        return list(actions)

    @staticmethod
    def _get_initial_state(traces: TraceList):
        # All traces should share an initial state (state of step 0)
        return traces[0][0].state

    @staticmethod
    def _get_goal(traces: TraceList):
        # Infer the goal from the final states
        final_states = []
        for trace in traces:
            final_states.append(trace[-1].state.fluents)

        # This will only work if the states share the same fluent objects
        # I think they should, but if not will need to use loops to find
        # overlapping fluents (name, value)
        return State(list(set(final_states[0]).intersection(*final_states)))

    @staticmethod
    def _extract_observer(traces: TraceList):
        fluents = Extract._get_fluents(traces)
        actions = Extract._get_actions(traces)
        initial_state = Extract._get_initial_state(traces)
        goal = Extract._get_goal(traces)
        return Model(fluents, actions, initial_state, goal)
