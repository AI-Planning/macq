from collections import defaultdict
from dataclasses import field
from typing import List

from attr import dataclass
from .model import Model
from ..trace import TraceList, DeltaState, State, Fluent


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
        action_effects = defaultdict(lambda: defaultdict(list))
        for trace in traces:
            for action in trace.actions:
                if action is not None:
                    sas_triples = trace.get_sas_triples(action)
                    for sas in sas_triples:
                        delta = sas.pre_state.diff_from(sas.post_state)
                        action_effects[action]["pre_states"].append(sas.pre_state)
                        action_effects[action]["add"].append(delta.added)
                        action_effects[action]["delete"].append(delta.deleted)

        for action, effects in action_effects.items():
            precond = Observer._get_preconditions(action_effects[action]["pre_states"])
            # action.update_precond(precond)
            add = set.intersection(*effects["add"])
            action.update_add(add)
            delete = set.intersection(*effects["delete"])
            action.update_delete(delete)

        print("=" * 100)
        indent = " " * 2
        for action in action_effects.keys():
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

            print()

        return []

    @staticmethod
    def _get_preconditions(pre_states: list[State]) -> set[Fluent]:
        # (positive) intersection of States -> set of fluents
        pass
