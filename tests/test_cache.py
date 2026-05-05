import pytest

from bioagentx.core.cache import AsyncTTLCache


@pytest.mark.asyncio
async def test_cache_set_and_get() -> None:
    cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60)
    await cache.set("key1", "value1")

    assert await cache.get("key1") == "value1"


@pytest.mark.asyncio
async def test_cache_miss() -> None:
    cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60)

    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_cache_evicts_oldest_on_max_size() -> None:
    cache: AsyncTTLCache[int] = AsyncTTLCache(ttl_seconds=60, max_size=3)
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)
    await cache.set("d", 4)

    assert await cache.get("a") is None
    assert await cache.get("d") == 4
    assert len(cache) == 3


@pytest.mark.asyncio
async def test_cache_clear() -> None:
    cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60)
    await cache.set("x", "y")
    await cache.clear()

    assert await cache.get("x") is None
    assert len(cache) == 0
