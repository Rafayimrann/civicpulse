"""
/health, /ready, /metrics.

/health and /ready are deliberately different: Kubernetes restarts a pod on
a failing liveness probe and removes it from the Service on a failing
readiness probe. /health must never touch the database or Redis - a slow
database would otherwise turn into a restart loop across the whole
deployment. /ready is exactly the opposite: it exists to check them.
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.db import check_db_connection

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    # Liveness: the process can respond. No I/O to anything external.
    return {"status": "alive"}


@router.get("/ready")
async def ready(response: Response, request: Request) -> dict:
    db_ok = await check_db_connection()
    redis_ok = await request.app.state.cache_provider.ping()

    if db_ok and redis_ok:
        return {"status": "ready", "postgres": "ok", "redis": "ok"}

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    failed = []
    if not db_ok:
        failed.append("postgres")
    if not redis_ok:
        failed.append("redis")
    return {"status": "not_ready", "failed_dependencies": failed}


@router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
