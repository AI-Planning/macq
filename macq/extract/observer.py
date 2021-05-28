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
        delta_states = defaultdict(list)
        actions = set()
        for trace in traces:
            for action in trace.actions:
                if action is not None:
                    actions.add(action)
                    sas_triples = trace.get_sas_triples(action)
                    for sas in sas_triples:
                        delta = sas.pre_state.diff_from(sas.post_state)
                        delta_states[action].append(delta)

        for action, deltas in delta_states.items():
            precond = set.intersection(*[delta.precond for delta in deltas])
            action.update_precond(precond)
            add = set.intersection(*[delta.added for delta in deltas])
            action.update_add(add)
            delete = set.intersection(*[delta.deleted for delta in deltas])
            action.update_delete(delete)

        indent = " " * 2
        for action in actions:
            print(action)
            print(f"{indent}precond:")
            for precond in action.precond:
                print(f"{indent*2}{precond}")
            print(f"{indent}add:")
            for add in action.add:
                print(f"{indent*2}{add}")
            print(f"{indent}delete:")
            for delete in action.delete:
                print(f"{indent*2}{delete}")

            # TODO
            # fix logic if necessary
            # test actions are updated correct
            # fix serialization
            # test Observer extraction
            # update all docstrings
            # make objects and fluents immutable

            # print("Delta states:")
            # for action, delta in delta_states.items():
            #     print(f"{indent}Action: {action}")
            #     if delta.pre_cond is not None:
            #         print(f"{indent*3}pre_cond:")
            #         for f in delta.pre_cond:
            #             print(f"{indent*4}{f}")
            #     if delta.added is not None:
            #         print(f"{indent * 3}added:")
            #         for f in delta.added:
            #             print(f"{indent* 4}{f}")
            #     if delta.deleted is not None:
            #         print(f"{indent*3}deleted:")
            #         for f in delta.deleted:
            #             print(f"{indent*4}{f}")

            print()

        return []
