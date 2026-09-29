"""
HTTP layer for /api/complaints. Parses, validates, serialises, sets status
codes. No business logic, no SQL - everything delegates to ComplaintService.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.dependencies import get_complaint_service, get_rate_limiter, get_stats_service
from app.models import Category, Priority, Status as ComplaintStatus
from app.providers.rate_limiter import RateLimiter
from app.schemas import ComplaintCreate, ComplaintListOut, ComplaintOut, StatusUpdate
from app.services.complaint_service import ComplaintNotFoundError, ComplaintService
from app.services.stats_service import StatsService
from app.services.state_machine import InvalidTransitionError

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _client_identifier(request: Request) -> str:
    # X-Forwarded-For first (behind nginx/ingress), then the direct peer.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ComplaintOut)
async def create_complaint(
    payload: ComplaintCreate,
    request: Request,
    response: Response,
    service: ComplaintService = Depends(get_complaint_service),
    stats_service: StatsService = Depends(get_stats_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ComplaintOut:
    identifier = _client_identifier(request)
    limit_result = await rate_limiter.check(identifier)
    if not limit_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down.",
            headers={"Retry-After": str(limit_result.retry_after_seconds)},
        )

    complaint = await service.create_complaint(
        text=payload.text, location=payload.location, reporter_contact=payload.reporter_contact
    )

    # Explicit invalidation on write, per the brief - don't wait for the TTL.
    await stats_service.invalidate()

    return ComplaintOut.model_validate(complaint)


@router.get("", response_model=ComplaintListOut)
async def list_complaints(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Category | None = Query(default=None),
    priority: Priority | None = Query(default=None),
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintListOut:
    items, total = await service.list_complaints(
        page=page, page_size=page_size, category=category, priority=priority, status=status_filter
    )
    return ComplaintListOut(
        items=[ComplaintOut.model_validate(c) for c in items], total=total, page=page, page_size=page_size
    )


@router.get("/{complaint_id}", response_model=ComplaintOut)
async def get_complaint(
    complaint_id: uuid.UUID, service: ComplaintService = Depends(get_complaint_service)
) -> ComplaintOut:
    try:
        complaint = await service.get_complaint(complaint_id)
    except ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return ComplaintOut.model_validate(complaint)


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
async def update_status(
    complaint_id: uuid.UUID,
    payload: StatusUpdate,
    service: ComplaintService = Depends(get_complaint_service),
    stats_service: StatsService = Depends(get_stats_service),
) -> ComplaintOut:
    try:
        complaint = await service.update_status(complaint_id, payload.status)
    except ComplaintNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    await stats_service.invalidate()
    return ComplaintOut.model_validate(complaint)
