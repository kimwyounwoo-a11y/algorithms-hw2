"""A string-keyed hash table using linear probing."""

import math
from typing import Generic, TypeVar


_Value = TypeVar("_Value")
_DELETED = object()


class LinearProbingTable(Generic[_Value]):
    """Store keys by probing consecutive slots from their Horner hash index."""

    _INITIAL_CAPACITY = 8

    def __init__(
        self, capacity: int = _INITIAL_CAPACITY, max_load: float | None = 0.75
    ):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if max_load is not None:
            if isinstance(max_load, bool) or not isinstance(max_load, (int, float)):
                raise TypeError("max_load must be a positive number or None")
            if max_load <= 0 or not math.isfinite(max_load):
                raise ValueError("max_load must be positive and finite or None")

        self._slots: list[_Entry[_Value] | object | None] = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self) -> int:
        return len(self._slots)

    @property
    def load_factor(self) -> float:
        return self._size / len(self._slots)

    def _hash_index(self, key: str, capacity: int | None = None) -> int:
        modulus = capacity if capacity is not None else len(self._slots)
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % modulus
        return value

    def _find_slot(self, key: str) -> tuple[int | None, int, int | None]:
        start = self._hash_index(key)
        first_deleted = None
        for offset in range(len(self._slots)):
            index = (start + offset) % len(self._slots)
            entry = self._slots[index]
            if entry is None:
                return None, index, first_deleted
            if entry is _DELETED:
                if first_deleted is None:
                    first_deleted = index
            elif entry.key == key:
                return index, index, first_deleted
        return None, start, first_deleted

    def put(self, key: str, value: _Value) -> None:
        found, empty, first_deleted = self._find_slot(key)
        if found is not None:
            entry = self._slots[found]
            entry.value = value
            return

        index = first_deleted if first_deleted is not None else empty
        if self._slots[index] is not None and self._slots[index] is not _DELETED:
            raise OverflowError("hash table is full")

        self._slots[index] = _Entry(key, value)
        self._size += 1
        if self._max_load is not None and self.load_factor > self._max_load:
            self._resize()

    def find(self, key: str) -> _Value:
        """Return the value for key, raising KeyError when key is absent."""
        found, _, _ = self._find_slot(key)
        if found is None:
            raise KeyError(key)
        entry = self._slots[found]
        return entry.value

    def get(self, key: str) -> _Value:
        return self.find(key)

    def contains(self, key: str) -> bool:
        found, _, _ = self._find_slot(key)
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
            if entry is not _DELETED and entry.key == key:
                return offset + 1
        return len(self._slots)

    def delete(self, key: str) -> None:
        found, _, _ = self._find_slot(key)
        if found is None:
            raise KeyError(key)
        self._slots[found] = _DELETED
        self._size -= 1

    def _resize(self) -> None:
        old_slots = self._slots
        self._slots = [None] * (len(old_slots) * 2)
        self._size = 0
        for entry in old_slots:
            if entry is not None and entry is not _DELETED:
                self._insert_without_resize(entry.key, entry.value)

    def _insert_without_resize(self, key: str, value: _Value) -> None:
        start = self._hash_index(key)
        for offset in range(len(self._slots)):
            index = (start + offset) % len(self._slots)
            if self._slots[index] is None:
                self._slots[index] = _Entry(key, value)
                self._size += 1
                return
        raise OverflowError("hash table is full")

    def __len__(self) -> int:
        return self._size


class _Entry(Generic[_Value]):
    __slots__ = ("key", "value")

    def __init__(self, key: str, value: _Value):
        self.key = key
        self.value = value
