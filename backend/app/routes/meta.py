from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_triage_service
from app.schemas import ProvidersMetaOut
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersMetaOut)
async def get_providers_meta(triage_service: TriageService = Depends(get_triage_service)) -> ProvidersMetaOut:
    return ProvidersMetaOut(
        active_provider=triage_service.active_provider_name,
        recent_outcomes=triage_service.recent_outcomes(),  # ring buffer is process-local telemetry
    )
