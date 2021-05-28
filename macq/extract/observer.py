from collections import defaultdict
from .model import Model
from ..trace import TraceList


class Observer:
    def __new__(cls, traces: TraceList):
        fluents = Observer._get_fluents(traces)
        actions = Observer._get_actions(traces)
        return Model(fluents, actions)

    @staticmethod
    def _get_fluents(traces: TraceList):
        fluents = set()
        for trace in traces:
            for fluent in trace.fluents:
                fluents.add(fluent)
        return list(fluents)

    @staticmethod
    def _get_actions(traces: TraceList):
        action_effects = defaultdict(lambda: defaultdict(set))
        for trace in traces:
            for action in trace.actions:
                if action is not None:
                    sas_triples = trace.get_sas_triples(action)
                    for sas in sas_triples:
                        action_effects[action]["pre_states"].add(sas.pre_state)
                        delta = sas.pre_state.diff_from(sas.post_state)
                        action_effects[action]["add"].update(delta.added)
                        action_effects[action]["delete"].update(delta.deleted)

        for action, effects in action_effects.items():
            precond = set.intersection(
                *map(Observer._get_true_fluents, action_effects[action]["pre_states"])
            )
            action.update_precond(precond)

            action.update_add(effects["add"])
            action.update_delete(effects["delete"])

        return [action for action in action_effects.keys()]

    @staticmethod
    def _get_true_fluents(state):
        true_fluents = set()
        for fluent, is_true in state.items():
            if is_true:
                true_fluents.add(fluent)
        return true_fluents
