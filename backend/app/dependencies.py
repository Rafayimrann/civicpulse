"""
FastAPI dependency wiring. Routes depend on these functions, never on
concrete provider/repository classes directly - that's what keeps routes
swappable and testable (see tests/conftest.py, which overrides several of
these with in-memory doubles).
"""
from __future__ import annotations


from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.providers.cache_provider import CacheProvider
from app.providers.rate_limiter import RateLimiter
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import ComplaintService
from app.services.stats_service import StatsService
from app.services.triage_service import TriageService


def get_app_settings() -> Settings:
    return get_settings()


def get_cache_provider(request: Request) -> CacheProvider:
    return request.app.state.cache_provider


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def get_triage_service(request: Request) -> TriageService:
    return request.app.state.triage_service


async def get_complaint_repository(session: AsyncSession = Depends(get_db)) -> ComplaintRepository:
    return ComplaintRepository(session)


async def get_complaint_service(
    repo: ComplaintRepository = Depends(get_complaint_repository),
    triage_service: TriageService = Depends(get_triage_service),
) -> ComplaintService:
    return ComplaintService(repo, triage_service)


async def get_stats_service(
    repo: ComplaintRepository = Depends(get_complaint_repository),
    cache: CacheProvider = Depends(get_cache_provider),
    settings: Settings = Depends(get_app_settings),
) -> StatsService:
    return StatsService(repo, cache, settings.stats_cache_ttl_seconds)
