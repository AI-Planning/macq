from collections import defaultdict
from .model import Model
from ..trace import TraceList, DeltaState


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
        delta_states = defaultdict(DeltaState)
        for trace in traces:
            for action in trace.actions:
                if action is not None:
                    sas_triples = trace.get_sas_triples(action)  # list
                    for sas in sas_triples:
                        delta = sas.pre_state.diff_from(sas.post_state)
                        delta_states[action].pre_cond.update(delta.pre_cond)
                        delta_states[action].added.update(delta.added)
                        delta_states[action].deleted.update(delta.deleted)

        print("Delta states:")
        indent = " " * 2
        for action, delta in delta_states.items():
            print(f"{indent}Action: {action}")
            if delta.pre_cond is not None:
                print(f"{indent*3}pre_cond:")
                for f in delta.pre_cond:
                    print(f"{indent*4}{f}")
            if delta.added is not None:
                print(f"{indent * 3}added:")
                for f in delta.added:
                    print(f"{indent* 4}{f}")
            if delta.deleted is not None:
                print(f"{indent*3}deleted:")
                for f in delta.deleted:
                    print(f"{indent*4}{f}")

            print()

        return []
