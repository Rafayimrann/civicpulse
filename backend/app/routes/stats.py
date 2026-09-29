from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_stats_service
from app.schemas import StatsOut
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
async def get_stats(response: Response, service: StatsService = Depends(get_stats_service)) -> StatsOut:
    stats, cache_hit = await service.get_stats()
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return stats
