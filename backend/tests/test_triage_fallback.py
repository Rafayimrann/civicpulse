"""
"Write this test if you write no other": given a provider that always
raises, POST /api/complaints still returns 201 and triaged_by == 'rules:fallback'.
"""
import pytest

from app.providers.triage.simulated import SimulatedTriage
from app.services.triage_service import TriageOutcomeStore, TriageService


@pytest.mark.asyncio
async def test_post_complaint_survives_triage_provider_failure(
    app_client_with_failing_triage, sample_complaint_payload
):
    resp = await app_client_with_failing_triage.post("/api/complaints", json=sample_complaint_payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["triaged_by"] == "rules:fallback"
    # Fallback still produced a valid, schema-conforming classification -
    # never a null/empty category just because the primary provider failed.
    assert body["category"] in {"water", "electricity", "sanitation", "roads", "streetlights", "other"}
    assert body["priority"] in {"high", "normal", "low"}
    assert body["ai_summary"] is not None


@pytest.mark.asyncio
async def test_fallback_is_recorded_in_provider_meta_outcomes(app_client_with_failing_triage, sample_complaint_payload):
    await app_client_with_failing_triage.post("/api/complaints", json=sample_complaint_payload)

    resp = await app_client_with_failing_triage.get("/api/meta/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_provider"] == "simulated"
    assert len(body["recent_outcomes"]) == 1
    assert body["recent_outcomes"][0]["provider"] == "rules:fallback"
    assert body["recent_outcomes"][0]["fallback"] is True


@pytest.mark.asyncio
async def test_triage_service_unit_falls_back_on_error():
    """Unit-level equivalent, isolated from the HTTP layer entirely."""
    failing_provider = SimulatedTriage(force_failure=True)
    service = TriageService(failing_provider, TriageOutcomeStore())

    import uuid

    result, triaged_by, latency_ms = await service.triage(
        "Burst pipe flooding the street", "Street 1", uuid.uuid4()
    )

    assert triaged_by == "rules:fallback"
    assert result.category is not None
    assert latency_ms >= 0
