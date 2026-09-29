"""
Pydantic v2 schemas.

These serve two purposes with one mental model, per the brief: validating
HTTP input/output, and validating LLM output (TriageResult). Never trust a
model response just because you asked nicely - it goes through the same
schema as anything else.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Category, Priority, Status

# ---------------------------------------------------------------------------
# Triage contract (providers/)
# ---------------------------------------------------------------------------


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("summary")
    @classmethod
    def _strip_and_bound(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 140:
            v = v[:140]
        return v


# ---------------------------------------------------------------------------
# Complaint I/O
# ---------------------------------------------------------------------------


class ComplaintCreate(BaseModel):
    text: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=3, max_length=200)
    reporter_contact: str | None = Field(default=None, max_length=200)


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime


class ComplaintListOut(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    status: Status


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class StatsOut(BaseModel):
    total: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]
    generated_at: datetime


# ---------------------------------------------------------------------------
# Meta / observability
# ---------------------------------------------------------------------------


class TriageOutcome(BaseModel):
    complaint_id: uuid.UUID
    provider: str
    latency_ms: int
    fallback: bool
    timestamp: datetime


class ProvidersMetaOut(BaseModel):
    active_provider: str
    recent_outcomes: list[TriageOutcome]


# ---------------------------------------------------------------------------
# Error body (field-level validation errors, 409 messages)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    detail: str
    errors: list[ErrorDetail] | None = None
