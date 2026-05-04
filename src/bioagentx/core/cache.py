import time
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CacheEntry(Generic[T]):
    value: T
    expires_at: float


class AsyncTTLCache(Generic[T]):
    """Small async-friendly TTL cache for deterministic tool and retrieval results."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[Hashable, CacheEntry[T]] = {}

    async def get(self, key: Hashable) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.time():
            self._store.pop(key, None)
            return None
        return entry.value

    async def set(self, key: Hashable, value: T) -> None:
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + self.ttl_seconds)

    async def clear(self) -> None:
        self._store.clear()
