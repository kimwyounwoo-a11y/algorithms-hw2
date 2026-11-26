"""A fixed-capacity string-keyed hash table using linear probing."""

from collections.abc import Iterator
from typing import Generic, TypeVar


_Value = TypeVar("_Value")


class TableFullError(OverflowError, RuntimeError):
    """Raised when insertion cannot find an available slot."""


class _Entry(Generic[_Value]):
    __slots__ = ("key", "value")

    def __init__(self, key: str, value: _Value):
        self.key = key
        self.value = value


class LinearProbingTable(Generic[_Value]):
    """Store keys by probing consecutive slots from their Horner hash index."""

    _INITIAL_CAPACITY = 64

    def __init__(self, capacity: int = _INITIAL_CAPACITY, max_load: None = None):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if max_load is not None:
            raise ValueError("linear probing uses a fixed capacity")

        self._slots: list[_Entry[_Value] | None] = [None] * capacity
        self._size = 0

    @property
    def capacity(self) -> int:
        return len(self._slots)

    @property
    def load_factor(self) -> float:
        return self._size / len(self._slots)

    def _hash_index(self, key: str) -> int:
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % len(self._slots)
        return value

    def _find_slot(self, key: str) -> tuple[int | None, int | None]:
        start = self._hash_index(key)
        for offset in range(len(self._slots)):
            index = (start + offset) % len(self._slots)
            entry = self._slots[index]
            if entry is None:
                return None, index
            if entry.key == key:
                return index, index
        return None, None

    def put(self, key: str, value: _Value) -> None:
        found, empty = self._find_slot(key)
        if found is not None:
            entry = self._slots[found]
            entry.value = value
            return
        if empty is None:
            raise TableFullError("hash table is full")

        self._slots[empty] = _Entry(key, value)
        self._size += 1

    def find(self, key: str) -> _Value:
        """Return the value for key, raising KeyError when key is absent."""
        found, _ = self._find_slot(key)
        if found is None:
            raise KeyError(key)
        return self._slots[found].value

    def get(self, key: str) -> _Value:
        return self.find(key)

    def contains(self, key: str) -> bool:
        found, _ = self._find_slot(key)
        return found is not None

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self.contains(key)

    def probe_count(self, key: str) -> int:
        start = self._hash_index(key)
        for offset in range(len(self._slots)):
            index = (start + offset) % len(self._slots)
            entry = self._slots[index]
            if entry is None:
                return offset + 1
            if entry.key == key:
                return offset + 1
        return len(self._slots)

    def iter_slots(self) -> Iterator[tuple[int, str | None, _Value | None]]:
        """Yield each slot index, key, and value, including empty slots."""
        for index, entry in enumerate(self._slots):
            if entry is None:
                yield index, None, None
            else:
                yield index, entry.key, entry.value

    def hash_steps(self, key: str) -> tuple[tuple[str, int, int], ...]:
        """Return each Horner step as (character, previous value, new value)."""
        value = 0
        steps = []
        for character in key:
            previous = value
            value = (value * 31 + ord(character)) % len(self._slots)
            steps.append((character, previous, value))
        return tuple(steps)

    def delete(self, key: str) -> None:
        found, _ = self._find_slot(key)
        if found is None:
            raise KeyError(key)
        self._slots[found] = None
        self._size -= 1
        following_entries = []
        index = (found + 1) % len(self._slots)
        while self._slots[index] is not None:
            entry = self._slots[index]
            self._slots[index] = None
            self._size -= 1
            following_entries.append(entry)
            index = (index + 1) % len(self._slots)
        for entry in following_entries:
            self.put(entry.key, entry.value)

    def __len__(self) -> int:
        return self._size
