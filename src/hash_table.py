"""A string-keyed hash table using separate chaining."""

import math
from collections.abc import Iterator
from typing import Generic, TypeVar


_Value = TypeVar("_Value")


class _Node(Generic[_Value]):
    __slots__ = ("key", "value", "next")

    def __init__(
        self, key: str, value: _Value, next_node: "_Node[_Value] | None" = None
    ):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable(Generic[_Value]):
    """Store string keys in buckets with Horner hashing and linked chains."""

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

        self._buckets: list[_Node[_Value] | None] = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    def _bucket_index(self, key: str, capacity: int) -> int:
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % capacity
        return value

    def put(self, key: str, value: _Value) -> None:
        index = self._bucket_index(key, len(self._buckets))
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1
        if (
            self._max_load is not None
            and self._size / len(self._buckets) > self._max_load
        ):
            self._resize()

    def get(self, key: str) -> _Value:
        node = self._buckets[self._bucket_index(key, len(self._buckets))]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        raise KeyError(key)

    def contains(self, key: str) -> bool:
        node = self._buckets[self._bucket_index(key, len(self._buckets))]
        while node is not None:
            if node.key == key:
                return True
            node = node.next
        return False

    def find(self, key: str) -> _Value:
        """Return the value for key, raising KeyError when key is absent."""
        return self.get(key)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self.contains(key)

    @property
    def load_factor(self) -> float:
        return self._size / len(self._buckets)

    def probe_count(self, key: str) -> int:
        """Return the number of chain nodes inspected when searching for key."""
        node = self._buckets[self._bucket_index(key, len(self._buckets))]
        probes = 0
        while node is not None:
            probes += 1
            if node.key == key:
                return probes
            node = node.next
        return probes

    def iter_bucket_items(self, index: int) -> Iterator[tuple[str, _Value]]:
        """Yield the key/value pairs in one bucket, in chain order."""
        if index < 0 or index >= len(self._buckets):
            raise IndexError(index)
        node = self._buckets[index]
        while node is not None:
            yield node.key, node.value
            node = node.next

    def hash_steps(self, key: str) -> tuple[tuple[str, int, int], ...]:
        """Return each Horner step as (character, previous value, new value)."""
        value = 0
        steps = []
        for character in key:
            previous = value
            value = (value * 31 + ord(character)) % len(self._buckets)
            steps.append((character, previous, value))
        return tuple(steps)

    def delete(self, key: str) -> None:
        index = self._bucket_index(key, len(self._buckets))
        previous = None
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                if previous is None:
                    self._buckets[index] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return
            previous = node
            node = node.next
        raise KeyError(key)

    def _resize(self) -> None:
        old_buckets = self._buckets
        self._buckets = [None] * (len(old_buckets) * 2)
        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next
                index = self._bucket_index(node.key, len(self._buckets))
                node.next = self._buckets[index]
                self._buckets[index] = node
                node = next_node

    def __len__(self) -> int:
        return self._size
