"""A string-keyed hash table using separate chaining."""

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
    _MAX_LOAD_NUMERATOR = 3
    _MAX_LOAD_DENOMINATOR = 4

    def __init__(self):
        self._buckets: list[_Node[_Value] | None] = [None] * self._INITIAL_CAPACITY
        self._size = 0

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
        if self._size * self._MAX_LOAD_DENOMINATOR > (
            len(self._buckets) * self._MAX_LOAD_NUMERATOR
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
