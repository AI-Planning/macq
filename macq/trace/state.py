from . import Fluent


class State:
    """
    Class for a State, which is the set of all fluents and their values at a particular Step.

    Arguments
    ---------
    fluents : List of Fluents
            A list of fluents representing the state.
    """

    def __init__(self, fluents: dict[Fluent, bool] = {}):
        self.fluents = fluents

    def __len__(self):
        return len(self.fluents)

    def __setitem__(self, key: Fluent, value: bool):
        self.fluents[key] = value

    def __getitem__(self, key: Fluent):
        return self.fluents[key]

    def __delitem__(self, key: Fluent):
        del self.fluents[key]

    def __repr__(self):
        return repr(self.fluents)

    def __str__(self):
        return str(self.fluents)

    def clear(self):
        return self.fluents.clear()

    def copy(self):
        return self.fluents.copy()

    def has_key(self, k):
        return k in self.fluents

    def update(self, *args, **kwargs):
        return self.fluents.update(*args, **kwargs)

    def keys(self):
        return self.fluents.keys()

    def values(self):
        return self.fluents.values()

    def items(self):
        return self.fluents.items()
