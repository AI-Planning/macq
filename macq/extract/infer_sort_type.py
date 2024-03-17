from ..observation import ObservedTraceList
from ..trace.fluent import PlanningObject
from ..trace.action import Action


def type_inference(obs_trace_list: ObservedTraceList) -> (dict[PlanningObject, str]):
    object_2_sort: dict[PlanningObject, str] = dict()
    actions: set[Action] = obs_trace_list.get_actions()
    objects: set[PlanningObject] = set()
    action_index_type: dict[str, list[set[str]]] = dict()
    for act in actions:
        objects.update(act.obj_params)
        if act.name not in action_index_type.keys():
            action_index_type[act.name] = list()
            for _ in act.obj_params:
                action_index_type[act.name].append(set())
        for index, obj in enumerate(act.obj_params):
            action_index_type[act.name][index].add(obj.name)

    ob_types: list[str] = list([ob.name for ob in objects])
    union_sorts_set: DisjointSet = DisjointSet(len(ob_types))
    for param_type_listOf_set in action_index_type.values():
        for s in param_type_listOf_set:
            t1: str = s.pop()
            s.add(t1)
            for t2 in s:
                union_sorts_set.union_by_rank(ob_types.index(t1), ob_types.index(t2))

    for obj in objects:
        object_2_sort[obj] = ob_types[union_sorts_set.find(ob_types.index(str(obj.name)))]

    return object_2_sort


class DisjointSet:
    def __init__(self, size):
        self.parent = [i for i in range(size)]
        self.rank = [0] * size

    # Function to find the representative (or the root node) of a set
    def find(self, i):
        # If i is not the representative of its set, recursively find the representative
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    # Unites the set that includes i and the set that includes j by rank
    def union_by_rank(self, i, j):
        # Find the representatives (or the root nodes) for the set that includes i and j
        irep = self.find(i)
        jrep = self.find(j)

        # Elements are in the same set, no need to unite anything
        if irep == jrep:
            return

        # Get the rank of i's tree
        irank = self.rank[irep]

        # Get the rank of j's tree
        jrank = self.rank[jrep]

        # If i's rank is less than j's rank
        if irank < jrank:
            # Move i under j
            self.parent[irep] = jrep
        # Else if j's rank is less than i's rank
        elif jrank < irank:
            # Move j under i
            self.parent[jrep] = irep
        # Else if their ranks are the same
        else:
            # Move i under j (doesn't matter which one goes where)
            self.parent[irep] = jrep
            # Increment the result tree's rank by 1
            self.rank[jrep] += 1
