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
        delta_states = defaultdict(list)
        for trace in traces:
            for action in trace.actions:
                if action is not None:
                    sas_triples = trace.get_sas_triples(action)
                    for sas in sas_triples:
                        delta_states[action].append(
                            sas.pre_state.diff_from(sas.post_state)
                        )

        print("Delta states:")
        indent = " " * 2
        for a, d in delta_states.items():
            print(f"{indent}Action: {a}")
            for i, l in enumerate(d):
                print(f"{indent * 2}trace {i}:")
                if l.pre_cond is not None:
                    print(f"{indent*3}pre_cond:")
                    for f in l.pre_cond:
                        print(f"{indent*4}{f}")
                if l.added is not None:
                    print(f"{indent * 3}added:")
                    for f in l.added:
                        print(f"{indent* 4}{f}")
                if l.deleted is not None:
                    print(f"{indent*3}deleted:")
                    for f in l.deleted:
                        print(f"{indent*4}{f}")

                print()

        return []
