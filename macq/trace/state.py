from __future__ import annotations
from typing import Dict
from rich.text import Text
from . import Fluent


class State:
    """State in a trace.

    A dict-like object. Maps `Fluent` objects to boolean values, representing
    the state for a `Step` in a `Trace`.

    Attributes:
        fluents (dict):
            A mapping of `Fluent` objects to their value in this state.
    """

    def __init__(self, fluents: Dict[Fluent, bool] = None):
        """Initializes State with an optional fluent-value mapping.

        Args:
            fluents (dict):
                Optional; A mapping of `Fluent` objects to their value in this
                state. Defaults to an empty `dict`.
        """
        self.fluents = fluents if fluents is not None else {}

    def __eq__(self, other):
        return isinstance(other, State) and self.fluents == other.fluents

    def __str__(self):
        return ", ".join([str(fluent) for (fluent, value) in self.items() if value])

    def __hash__(self):
        return hash(str(self.details()))

    def __len__(self):
        return len(self.fluents)

    def __setitem__(self, key: Fluent, value: bool):
        self.fluents[key] = value

    def __getitem__(self, key: Fluent):
        return self.fluents[key]

    def __delitem__(self, key: Fluent):
        del self.fluents[key]

    def __iter__(self):
        return iter(self.fluents)

    def __contains__(self, key):
        return self.fluents[key]

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

    def details(self):
        string = Text()
        for fluent, value in self.items():
            color = "green" if value else "red"
            string.append(f"{str(fluent)}", style=color)
            string.append(", ")
        return string[:-2]

    def clone(self, atomic=False):
        if atomic:
            return AtomicState({str(fluent): value for fluent, value in self.items()})
        return State(self.fluents.copy())

    def holds(self, fluent: str):
        fluents = dict(map(lambda f: (f.name, f), self.keys()))
        if fluent in fluents.keys():
            return self[fluents[fluent]]


class AtomicState(State):
    """A State where the fluents are represented by strings."""

    def __init__(self, fluents: Dict[str, bool] = None):
        self.fluents = fluents if fluents is not None else {}
