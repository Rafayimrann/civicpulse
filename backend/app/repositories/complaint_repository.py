"""
All SQL for the complaints table lives in this file and nowhere else.
routes/ never imports sqlalchemy; services/ never writes a query - they call
methods here and get back ORM objects or plain aggregates.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Complaint, Priority, Status


class ComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        text: str,
        location: str,
        reporter_contact: str | None,
        category: Category,
        priority: Priority,
        ai_summary: str | None,
        triaged_by: str,
        triage_latency_ms: int,
    ) -> Complaint:
        complaint = Complaint(
            id=uuid.uuid4(),
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=category,
            priority=priority,
            status=Status.open,
            ai_summary=ai_summary,
            triaged_by=triaged_by,
            triage_latency_ms=triage_latency_ms,
        )
        self._session.add(complaint)
        await self._session.flush()
        await self._session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: uuid.UUID) -> Complaint | None:
        return await self._session.get(Complaint, complaint_id)

    async def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        category: Category | None = None,
        priority: Priority | None = None,
        status: Status | None = None,
    ) -> tuple[list[Complaint], int]:
        filters = []
        if category is not None:
            filters.append(Complaint.category == category)
        if priority is not None:
            filters.append(Complaint.priority == priority)
        if status is not None:
            filters.append(Complaint.status == status)

        count_stmt = select(func.count()).select_from(Complaint)
        for f in filters:
            count_stmt = count_stmt.where(f)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = select(Complaint).order_by(Complaint.created_at.desc())
        for f in filters:
            stmt = stmt.where(f)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows), total

    async def update_status(self, complaint: Complaint, new_status: Status) -> Complaint:
        complaint.status = new_status
        complaint.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(complaint)
        return complaint

    async def aggregate_stats(self) -> dict:
        total = (await self._session.execute(select(func.count()).select_from(Complaint))).scalar_one()

        by_category_rows = await self._session.execute(
            select(Complaint.category, func.count()).group_by(Complaint.category)
        )
        by_priority_rows = await self._session.execute(
            select(Complaint.priority, func.count()).group_by(Complaint.priority)
        )
        by_status_rows = await self._session.execute(
            select(Complaint.status, func.count()).group_by(Complaint.status)
        )

        def _to_dict(rows) -> dict[str, int]:
            out: dict[str, int] = {}
            for key, count in rows:
                out[key.value if hasattr(key, "value") else str(key)] = count
            return out

        return {
            "total": total,
            "by_category": _to_dict(by_category_rows),
            "by_priority": _to_dict(by_priority_rows),
            "by_status": _to_dict(by_status_rows),
        }
