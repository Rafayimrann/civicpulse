"""
Test fixtures.

Provider pinning: TRIAGE_PROVIDER is pinned to SimulatedTriage for every
test in this suite, per the brief - a test suite that depends on a real LLM
is a test suite that is occasionally red for reasons that have nothing to
do with the code. SimulatedTriage is deterministic (same input -> same
output) and supports force_failure=True to exercise the fallback path
without needing a real flaky dependency.

DB: SQLite in-memory via aiosqlite, one fresh schema per test function via
Base.metadata.create_all() - this is the one place create_all() is
legitimate, because it's test-only scaffolding, not the real migration
path (which stays Alembic-only, see alembic/versions/).

Redis/rate limiter: in-memory doubles (InMemoryCacheProvider,
InMemoryRateLimiter) behind the exact same Protocol the real Redis-backed
classes implement, so the service layer under test never knows the
difference.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_db
from app.main import create_app
from app.providers.cache_provider import InMemoryCacheProvider
from app.providers.rate_limiter import InMemoryRateLimiter
from app.providers.triage.simulated import SimulatedTriage
from app.services.triage_service import TriageOutcomeStore, TriageService

RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def cache_provider() -> InMemoryCacheProvider:
    return InMemoryCacheProvider()


@pytest.fixture
def rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter(window_seconds=RATE_LIMIT_WINDOW, max_requests=RATE_LIMIT_MAX)


@pytest.fixture
def failing_triage_service() -> TriageService:
    """A TriageService whose primary provider always raises - used to test
    the fallback-to-rules path deterministically."""
    provider = SimulatedTriage(force_failure=True)
    return TriageService(provider, TriageOutcomeStore())


@pytest.fixture
def triage_service() -> TriageService:
    provider = SimulatedTriage(force_failure=False)
    return TriageService(provider, TriageOutcomeStore())


@pytest_asyncio.fixture
async def app_client(db_engine, cache_provider, rate_limiter, triage_service) -> AsyncGenerator[AsyncClient, None]:
    """A fully wired ASGI test client: real routes and services, in-memory
    doubles for Postgres (SQLite), Redis cache and the rate limiter, and
    SimulatedTriage pinned as the triage provider."""
    app = create_app()
    app.state.cache_provider = cache_provider
    app.state.rate_limiter = rate_limiter
    app.state.triage_service = triage_service

    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    async def _override_get_db():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def app_client_with_failing_triage(
    db_engine, cache_provider, rate_limiter, failing_triage_service
) -> AsyncGenerator[AsyncClient, None]:
    """Same as app_client, but the triage provider always raises - so every
    complaint created through this client goes through the fallback path."""
    app = create_app()
    app.state.cache_provider = cache_provider
    app.state.rate_limiter = rate_limiter
    app.state.triage_service = failing_triage_service

    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    async def _override_get_db():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def sample_complaint_payload() -> dict:
    return {
        "text": "Burst water main flooding the street since morning, water entering ground floor houses.",
        "location": "Street 12, Block C",
        "reporter_contact": "citizen@example.com",
    }
