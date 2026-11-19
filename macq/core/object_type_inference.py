"""Infers flat object types from where objects appear in observations."""

from typing import Dict, Iterable, List, Optional, Set


class DisjointSet:
    """Groups the integers below `size` into sets that can be merged."""

    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, i: int) -> int:
        """Returns the representative of the set containing `i`."""
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union_by_rank(self, i: int, j: int) -> None:
        """Merges the sets containing `i` and `j`."""
        i_root, j_root = self.find(i), self.find(j)
        if i_root == j_root:
            return
        if self.rank[i_root] < self.rank[j_root]:
            self.parent[i_root] = j_root
        elif self.rank[j_root] < self.rank[i_root]:
            self.parent[j_root] = i_root
        else:
            self.parent[i_root] = j_root
            self.rank[j_root] += 1


def _types_from_positions(object_names: Set[str], positions: Iterable[Set[str]]) -> Dict[str, str]:
    """Returns each object's type name, where objects sharing an argument position share a type."""
    objects: List[str] = list(object_names)
    index = {name: i for i, name in enumerate(objects)}
    groups = DisjointSet(len(objects))
    for position in positions:
        first, *others = position
        for other in others:
            groups.union_by_rank(index[first], index[other])

    roots = sorted({groups.find(i) for i in range(len(objects))})
    type_numbers = {root: number for number, root in enumerate(roots)}
    return {name: f"t{type_numbers[groups.find(index[name])]}" for name in objects}


def _argument_positions(named_arguments: Iterable) -> List[Set[str]]:
    """Returns the object names seen at each argument position of each (name, objects) pair."""
    positions: Dict[str, List[Set[str]]] = {}
    for name, objects in named_arguments:
        found = positions.setdefault(name, [set() for _ in objects])
        for position, obj in zip(found, objects):
            position.add(obj.name)
    return [position for found in positions.values() for position in found]


def infer_object_types_from_fluents(obs_trace_list, true_fluents: Optional[Set] = None) -> Dict[str, str]:
    """Infers each object's type from the argument positions of true fluents.

    This suits traces of untyped domains where predicates define the types, such as `(truck t1)`.

    Args:
        obs_trace_list:
            The observed trace list.
        true_fluents:
            Optional; The fluents to use instead of those true in some observed state.

    Returns:
        A dictionary mapping each object name to its inferred type name.
    """
    object_names: Set[str] = set()
    observed_true_fluents = set()
    for obs_trace in obs_trace_list.observations:
        for obs in obs_trace:
            if obs.state:
                for fluent, value in obs.state.items():
                    object_names.update(obj.name for obj in fluent.objects)
                    if value:
                        observed_true_fluents.add(fluent)

    fluents = true_fluents if true_fluents else observed_true_fluents
    object_names.update(obj.name for fluent in fluents for obj in fluent.objects)
    positions = _argument_positions((fluent.name, fluent.objects) for fluent in fluents)
    return _types_from_positions(object_names, positions)


def infer_object_types_from_actions(actions: Set) -> Dict[str, str]:
    """Infers each object's type from the argument positions of observed grounded actions.

    Args:
        actions:
            The grounded actions that were observed.

    Returns:
        A dictionary mapping each object name to its inferred type name.
    """
    object_names = {obj.name for action in actions for obj in action.objects}
    positions = _argument_positions((action.name, action.objects) for action in actions)
    return _types_from_positions(object_names, positions)
