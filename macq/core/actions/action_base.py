from typing import Hashable, Iterable


class _FluentSet:
    """An action attribute that always holds a set of fluents."""

    def __set_name__(self, owner, name):
        self._attribute = f"_{name}"

    def __get__(self, action, owner=None):
        return self if action is None else getattr(action, self._attribute)

    def __set__(self, action, fluents: Iterable):
        setattr(action, self._attribute, set(fluents))


class ActionBase:
    """The preconditions and effects shared by lifted and grounded actions.

    Preconditions and effects can be updated while an action is being learned. An action hashes on its
    signature, which never changes, and compares on its full contents.
    """

    positive_preconditions = _FluentSet()
    negative_preconditions = _FluentSet()
    add_effects = _FluentSet()
    delete_effects = _FluentSet()

    def __init__(
        self,
        name: str,
        positive_preconditions: Iterable = (),
        negative_preconditions: Iterable = (),
        add_effects: Iterable = (),
        delete_effects: Iterable = (),
    ):
        self._name = name
        self.positive_preconditions = positive_preconditions
        self.negative_preconditions = negative_preconditions
        self.add_effects = add_effects
        self.delete_effects = delete_effects

    @property
    def name(self) -> str:
        return self._name

    @property
    def signature(self) -> Hashable:
        raise NotImplementedError

    def _contents(self) -> tuple:
        return (
            self.name,
            self.positive_preconditions,
            self.negative_preconditions,
            self.add_effects,
            self.delete_effects,
        )

    def __eq__(self, other):
        return type(self) is type(other) and self._contents() == other._contents()

    def __hash__(self):
        return hash(self.signature)

    def details(self) -> str:
        raise NotImplementedError

    def __str__(self):
        return self.details()

    def __repr__(self):
        return self.details()
