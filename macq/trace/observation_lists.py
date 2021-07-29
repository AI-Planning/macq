from typing import Iterator, List, Type, Set
from . import Trace
from ..observation import Observation
import macq.trace as TraceAPI


class ObservationLists(TraceAPI.TraceList):
    traces: List[List[Observation]]
    # Disable methods
    generate_more = property()
    get_usage = property()
    tokenize = property()

    def __init__(self, traces: TraceAPI.TraceList, Token: Type[Observation], **kwargs):
        self.traces = []
        self.type = Token
        trace: Trace
        for trace in traces:
            tokens = trace.tokenize(Token, **kwargs)
            self.append(tokens)

    def get_actions(self):
        actions = set()
        for obs_list in self:
            for obs in obs_list:
                action = obs.action
                if action:
                    actions.add(action)
        return actions

    def get_fluents(self):
        fluents = set()
        for obs_list in self:
            for obs in obs_list:
                fluents.update(list(obs.state.keys()))
        return fluents

    def fetch_observations(self, query: dict):
        matches: List[Set[Observation]] = list()
        trace: List[Observation]
        for i, trace in enumerate(self):
            matches.append(set())
            for obs in trace:
                if obs.matches(query):  # if no matches, set can be empty
                    matches[i].add(obs)
        return matches  # list of sets of matching fluents from each trace

    def fetch_observation_windows(self, query: dict, left: int, right: int):
        windows = []
        matches = self.fetch_observations(query)
        trace: Set[Observation]
        for i, trace in enumerate(matches):  # note obs.index starts at 1 (index = i+1)
            for obs in trace:
                start = obs.index - left - 1
                end = obs.index + right
                windows.append(self[i][start:end])
        return windows

    def get_transitions(self, action: str):
        query = {"action": action}
        return self.fetch_observation_windows(query, 0, 1)

    def get_all_transitions(self):
        actions = self.get_actions()
        try:
            return {
                action: self.get_transitions(action.details()) for action in actions
            }
        except AttributeError:
            return {action: self.get_transitions(str(action)) for action in actions}
