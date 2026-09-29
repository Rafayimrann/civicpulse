"""
Stats aggregation with a Redis read-through cache.

Two invalidation mechanisms are deliberately layered: a 30s TTL (so a
forgotten invalidation self-heals) AND explicit invalidation on every write
(so a freshly submitted complaint appears in stats immediately rather than
up to 30s later). Either alone is defensible; together they cover both the
"someone forgot to call invalidate()" case and the "citizen expects to see
their own complaint counted now" case.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.providers.cache_provider import CacheProvider
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas import StatsOut

_STATS_CACHE_KEY = "stats:aggregate"


class StatsService:
    def __init__(self, repo: ComplaintRepository, cache: CacheProvider, ttl_seconds: int) -> None:
        self._repo = repo
        self._cache = cache
        self._ttl = ttl_seconds

    async def get_stats(self) -> tuple[StatsOut, bool]:
        """Returns (stats, cache_hit)."""
        cached = await self._cache.get(_STATS_CACHE_KEY)
        if cached is not None:
            data = json.loads(cached)
            return StatsOut.model_validate(data), True

        raw = await self._repo.aggregate_stats()
        stats = StatsOut(
            total=raw["total"],
            by_category=raw["by_category"],
            by_priority=raw["by_priority"],
            by_status=raw["by_status"],
            generated_at=datetime.now(timezone.utc),
        )
        await self._cache.set(_STATS_CACHE_KEY, stats.model_dump_json(), self._ttl)
        return stats, False

    async def invalidate(self) -> None:
        await self._cache.delete(_STATS_CACHE_KEY)
