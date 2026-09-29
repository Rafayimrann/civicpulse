"""
Middleware stack: propagate/generate X-Request-ID, log each request as one
structured JSON line, and record Prometheus request-count/latency metrics.
"""
from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import get_logger, request_id_ctx
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger("app.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception",
                extra={"path": request.url.path, "method": request.method},
            )
            raise
        finally:
            request_id_ctx.reset(token)

        duration = time.perf_counter() - start
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)

        REQUEST_COUNT.labels(method=request.method, path=route_path, status_code=response.status_code).inc()
        REQUEST_LATENCY.labels(method=request.method, path=route_path).observe(duration)

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )
        return response
