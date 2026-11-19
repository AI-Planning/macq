"""Cached hashes for the immutable parts of a domain model, which states and traces hash constantly."""


class CachedValue:
    """Caches the hash of `_value_key()`.

    Subclasses are frozen dataclasses declared with `eq=False`, which define `__eq__` on the same fields as
    `_value_key()` and set `__hash__ = CachedValue.__hash__`. The cached hash is left out of pickles and
    copies, because string hashes differ between processes.
    """

    __slots__ = ()

    def _value_key(self) -> tuple:
        raise NotImplementedError

    def __hash__(self):
        value = self.__dict__.get("_hash")
        if value is None:
            value = hash(self._value_key())
            object.__setattr__(self, "_hash", value)
        return value

    def __getstate__(self):
        state = dict(self.__dict__)
        state.pop("_hash", None)
        return state
