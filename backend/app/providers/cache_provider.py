"""
CacheProvider: a thin Protocol over Redis so services never import `redis`
directly. Backs two distinct jobs (per the brief, deliberately the same
infrastructure serving two purposes):
  1. read-through cache for /api/stats (30s TTL, explicit invalidation on write)
  2. content-hash cache for triage results (24h TTL)
"""
from __future__ import annotations

from typing import Protocol

import redis.asyncio as redis_asyncio

from app.config import get_settings


class CacheProvider(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def ping(self) -> bool: ...


class RedisCacheProvider:
    def __init__(self, client: redis_asyncio.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:
            return False


class InMemoryCacheProvider:
    """Test double: same interface, no network. Used by the pytest suite."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        # TTL intentionally not simulated - tests that need TTL semantics
        # exercise them via explicit delete() (invalidation), which is the
        # behaviour actually under test (see test_cache.py).
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True


_redis_client: redis_asyncio.Redis | None = None


def get_redis_client() -> redis_asyncio.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis_asyncio.from_url(settings.redis_url, decode_responses=False)
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
