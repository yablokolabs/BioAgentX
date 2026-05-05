import time
from collections import OrderedDict
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

_DEFAULT_MAX_SIZE = 2048


@dataclass(slots=True)
class CacheEntry(Generic[T]):
    """Single cached value with an absolute expiration timestamp."""

    value: T
    expires_at: float


class AsyncTTLCache(Generic[T]):
    """Async-friendly TTL + LRU cache with bounded memory.

    Entries expire after ``ttl_seconds`` and the cache evicts the least
    recently used entry when ``max_size`` is exceeded.
    """

    def __init__(self, ttl_seconds: int = 300, *, max_size: int = _DEFAULT_MAX_SIZE) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._store: OrderedDict[Hashable, CacheEntry[T]] = OrderedDict()

    async def get(self, key: Hashable) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.time():
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return entry.value

    async def set(self, key: Hashable, value: T) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + self.ttl_seconds)
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    async def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
