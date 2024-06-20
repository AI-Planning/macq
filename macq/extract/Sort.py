from ..observation import ObservedTraceList
from ..trace import Fluent, Action


class Sort:
    """clss representation of a sort matching the tarski lang representation"""
    sort_name: str
    parent: [str | None]

    def __init__( self, sort: str, parent: str=None):
        """if sort has a parent of type DomainSort, input the parent sort name
        if the sort has no learned parent, parent argument can remain empty"""
        self.sort_name = sort
        self.parent = parent

    def __eq__(self, other):
        return self.sort_name == other.sort_name and self.parent == other.parent

    def __hash__(self):
        return hash(self.details())

    def details(self):
        return f"name: {self.sort_name}, parent: {self.parent}"



def sort_by_observations(obs_trace_list: ObservedTraceList) -> (set[Sort], dict[str, str]):
    pass






def sort_inference_by_fluents(obs_trace_list: ObservedTraceList,
                              true_fluents: set[Fluent]=None ) -> (dict[str, str]):

    os: set[str] = set()  # set of object names
    if not true_fluents:
        true_fluents = set()
        for obs_trace in obs_trace_list.observations:
            for obs in obs_trace:
                if obs.state:
                    for f, v in obs.state.items():
                        os.update(obj.name for obj in f.objects)
                        if v:
                            true_fluents.add(f)


    objects: list[str] = list(os)  # list of object names
    f_index_type: dict[str, list[set[str]]] = dict()

    for f in true_fluents:
        if f.name not in f_index_type.keys():
            f_index_type[f.name] = list()
            for _ in f.objects:
                f_index_type[f.name].append(set())
        for index, obj in enumerate(f.objects):
            f_index_type[f.name][index].add(obj.name)

    union_sorts_set: DisjointSet = DisjointSet(len(objects))
    for param_type_listOf_set in f_index_type.values():
        for s in param_type_listOf_set:
            t1: str = s.pop()
            s.add(t1)
            for t2 in s:
                union_sorts_set.union_by_rank(objects.index(t1), objects.index(t2))

    ugly_sorts: list[int] = list({union_sorts_set.find(i) for i in range(len(objects))})
    ugly_sorts.sort()
    nicer_sorting: dict[int, int] = dict()
    for i in range(len(ugly_sorts)):
        nicer_sorting[ugly_sorts[i]] = i
    object_2_sort: dict[str, str] = dict()
    for obj in objects:
        ugly_sort = union_sorts_set.find(objects.index(obj))
        object_2_sort[obj] = f"t{nicer_sorting[ugly_sort]}"

    return object_2_sort


def sort_inference_by_action(actions: set[Action]) -> (dict[str, str]):
    os: set[str] = {obj.name for action in actions for obj in action.obj_params}

    objects: list[str] = list(os)  # list of object names
    act_index_type: dict[str, list[set[str]]] = dict()

    for a in actions:
        if a.name not in act_index_type.keys():
            act_index_type[a.name] = list()
            for _ in a.obj_params:
                act_index_type[a.name].append(set())
        for index, obj in enumerate(a.obj_params):
            act_index_type[a.name][index].add(obj.name)

    union_sorts_set: DisjointSet = DisjointSet(len(objects))
    for param_type_listOf_set in act_index_type.values():
        for s in param_type_listOf_set:
            t1: str = s.pop()
            s.add(t1)
            for t2 in s:
                union_sorts_set.union_by_rank(objects.index(t1), objects.index(t2))

    ugly_sorts: list[int] = list({union_sorts_set.find(i) for i in range(len(objects))})
    ugly_sorts.sort()
    nicer_sorting: dict[int, int] = dict()
    for i in range(len(ugly_sorts)):
        nicer_sorting[ugly_sorts[i]] = i
    object_2_sort: dict[str, str] = dict()
    for obj in objects:
        ugly_sort = union_sorts_set.find(objects.index(obj))
        object_2_sort[obj] = f"t{nicer_sorting[ugly_sort]}"

    return object_2_sort

class DisjointSet:  # this class was taken from geeksForGeeks
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
