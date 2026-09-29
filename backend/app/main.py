"""
Application entrypoint: builds providers/services once at startup, attaches
them to app.state for dependency injection, and handles graceful shutdown.

Graceful shutdown: uvicorn already intercepts SIGTERM and stops accepting
new connections while draining in-flight ones (that's what
`timeout_graceful_shutdown` controls). What we own on top of that is closing
our own resources - the DB pool and the Redis client - inside the lifespan's
shutdown phase, so they close cleanly after the drain rather than out from
under an in-flight request.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.config import get_settings
from app.db import dispose_engine
from app.logging_config import configure_logging, get_logger
from app.middleware import RequestContextMiddleware
from app.providers.cache_provider import RedisCacheProvider, close_redis_client, get_redis_client
from app.providers.rate_limiter import RedisFixedWindowRateLimiter
from app.providers.triage.factory import build_triage_provider
from app.routes import complaints, meta, stats, system
from app.schemas import ErrorDetail, ErrorResponse
from app.services.triage_service import TriageOutcomeStore, TriageService

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    redis_client = get_redis_client()
    cache_provider = RedisCacheProvider(redis_client)
    rate_limiter = RedisFixedWindowRateLimiter(
        redis_client,
        window_seconds=settings.rate_limit_window_seconds,
        max_requests=settings.rate_limit_max_requests,
    )
    triage_provider = build_triage_provider(settings, cache_provider)
    outcome_store = TriageOutcomeStore()
    triage_service = TriageService(triage_provider, outcome_store)

    app.state.cache_provider = cache_provider
    app.state.rate_limiter = rate_limiter
    app.state.triage_service = triage_service

    logger.info("CivicPulse backend started", extra={"triage_provider": settings.triage_provider})

    yield

    logger.info("CivicPulse backend shutting down - draining and closing pools")
    await close_redis_client()
    await dispose_engine()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Field-level validation errors, per the brief's 400 contract.
        errors = [
            ErrorDetail(field=".".join(str(p) for p in err["loc"][1:]), message=err["msg"])
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(detail="Validation failed", errors=errors).model_dump(),
        )

    app.include_router(complaints.router)
    app.include_router(stats.router)
    app.include_router(meta.router)
    app.include_router(system.router)

    return app


app = create_app()
