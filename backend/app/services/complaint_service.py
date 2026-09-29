"""
Complaint business logic: create (validate -> triage -> persist), read,
list, and status transitions. Routes call only this service; the service
calls the repository for persistence and the triage service for AI
classification. No SQL and no HTTP concerns live here.
"""
from __future__ import annotations

import uuid

from app.models import Category, Complaint, Priority, Status
from app.repositories.complaint_repository import ComplaintRepository
from app.services.state_machine import validate_transition
from app.services.triage_service import TriageService


class ComplaintNotFoundError(Exception):
    pass


class ComplaintService:
    def __init__(self, repo: ComplaintRepository, triage_service: TriageService) -> None:
        self._repo = repo
        self._triage = triage_service

    async def create_complaint(
        self, *, text: str, location: str, reporter_contact: str | None
    ) -> Complaint:
        # A temp id lets the triage outcome ring buffer reference the
        # complaint even though the row doesn't exist yet at triage time.
        provisional_id = uuid.uuid4()
        result, triaged_by, latency_ms = await self._triage.triage(text, location, provisional_id)

        return await self._repo.create(
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=result.category,
            priority=result.priority,
            ai_summary=result.summary,
            triaged_by=triaged_by,
            triage_latency_ms=latency_ms,
        )

    async def get_complaint(self, complaint_id: uuid.UUID) -> Complaint:
        complaint = await self._repo.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(str(complaint_id))
        return complaint

    async def list_complaints(
        self,
        *,
        page: int,
        page_size: int,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
    ) -> tuple[list[Complaint], int]:
        return await self._repo.list_paginated(
            page=page, page_size=page_size, category=category, priority=priority, status=status
        )

    async def update_status(self, complaint_id: uuid.UUID, new_status: Status) -> Complaint:
        complaint = await self.get_complaint(complaint_id)
        validate_transition(complaint.status, new_status)
        return await self._repo.update_status(complaint, new_status)
