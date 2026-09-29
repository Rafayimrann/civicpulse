"""
Distributed fixed-window rate limiter, keyed by client IP, backed by Redis.

Deliberately NOT an in-process counter: once the deployment is scaled to N
pods, an in-process limiter would allow N times the intended traffic. Redis
is the one shared piece of state every pod can see.

Algorithm: fixed window. Key = f"ratelimit:{client_ip}:{window_start}".
INCR the key; set an expiry equal to the window length on first increment
only. If the counter exceeds the configured max, the caller is over budget
for the remainder of the window.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

import redis.asyncio as redis_asyncio


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class RateLimiter(Protocol):
    async def check(self, identifier: str) -> RateLimitResult: ...


class RedisFixedWindowRateLimiter:
    def __init__(self, client: redis_asyncio.Redis, window_seconds: int, max_requests: int) -> None:
        self._client = client
        self._window = window_seconds
        self._max = max_requests

    async def check(self, identifier: str) -> RateLimitResult:
        now = int(time.time())
        window_start = now - (now % self._window)
        key = f"ratelimit:{identifier}:{window_start}"

        # Pipeline so INCR + EXPIRE happen atomically enough that a crash
        # between them can't leave a key with no TTL (worst case it just
        # gets a slightly generous expiry re-applied on the next hit).
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self._window)
        results = await pipe.execute()
        count = int(results[0])

        window_end = window_start + self._window
        retry_after = max(window_end - now, 1)

        if count > self._max:
            return RateLimitResult(allowed=False, remaining=0, retry_after_seconds=retry_after)
        return RateLimitResult(allowed=True, remaining=self._max - count, retry_after_seconds=retry_after)


class InMemoryRateLimiter:
    """Test double: identical fixed-window semantics, no Redis."""

    def __init__(self, window_seconds: int, max_requests: int) -> None:
        self._window = window_seconds
        self._max = max_requests
        self._counters: dict[str, tuple[int, int]] = {}  # identifier -> (window_start, count)

    async def check(self, identifier: str) -> RateLimitResult:
        now = int(time.time())
        window_start = now - (now % self._window)
        current = self._counters.get(identifier)

        if current is None or current[0] != window_start:
            count = 1
        else:
            count = current[1] + 1
        self._counters[identifier] = (window_start, count)

        window_end = window_start + self._window
        retry_after = max(window_end - now, 1)

        if count > self._max:
            return RateLimitResult(allowed=False, remaining=0, retry_after_seconds=retry_after)
        return RateLimitResult(allowed=True, remaining=self._max - count, retry_after_seconds=retry_after)
