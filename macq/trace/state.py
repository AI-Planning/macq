from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from . import Fluent


@dataclass
class DeltaState:
    pre_cond: set[Fluent] = field(default_factory=set)
    added: set[Fluent] = field(default_factory=set)
    deleted: set[Fluent] = field(default_factory=set)


class State:
    """State representation.

    A Dict-like object. Maps `Fluent` objects to boolean values, representing
    the state for a `Step` in a `Trace`.

    Attributes:
        fluents (dict): A mapping of `Fluent` objects to their value in this
        state.
    """

    def __init__(self, fluents: dict[Fluent, bool] = {}):
        """Initializes State with an optional fluent-value mapping.

        Args:
            fluents (dict): Optional; A mapping of `Fluent` objects to their
            value in this state. Defaults to an empty `dict`.
        """
        self.fluents = fluents

    def __str__(self):
        string = ""
        for fluent, value in self.items():
            string += f"{fluent.name} ({value}), "
        return string[:-2]

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
        return self.fluents.__contains__(key)

    def __repr__(self):
        return repr(self.fluents)

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

    def diff_from(self, other: Optional[State]):
        """Find the delta-state between this state and `other`.

        Args:
            other (State): The secondary state to compare this one to.

        Returns:
            A tuple with 3 entries. The first is the list of fluents that were
            added from this state to `other`. The second is the list of fluents
            that were deleted between this state and `other`. The third is a
            list of the fluents that are true in both states, ie. the
            preconditions


        """
        if other is None:
            return DeltaState(post_state=set(self.fluents.keys()))
        pre_cond = set()
        added = set()
        deleted = set()
        fluents = list(self.keys())
        fluents.extend(list(other.keys()))
        for f in fluents:
            if self.has_key(f) and other.has_key(f):  # fluent in both states
                if self[f] and other[f]:  # true in both states -> pre cond
                    pre_cond.add(f)
                elif self[f] and not other[f]:  # true pre, false post -> deleted
                    deleted.add(f)
                else:  # false pre, true post -> added
                    added.add(f)
            elif self.has_key(f):  # fluent in pre-state
                if self[f]:  # true -> pre cond
                    pre_cond.add(f)
                else:  # false -> nothing
                    pass
            else:  # fluent in post-state
                if other[f]:  # true -> added
                    added.add(f)
                else:  # false -> deleted
                    deleted.add(f)

        return DeltaState(pre_cond, added, deleted)
