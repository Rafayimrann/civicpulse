import uuid

import pytest


@pytest.mark.asyncio
async def test_create_complaint_returns_201_with_triage_fields(app_client, sample_complaint_payload):
    resp = await app_client.post("/api/complaints", json=sample_complaint_payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["text"] == sample_complaint_payload["text"]
    assert body["status"] == "open"
    assert body["category"] in {"water", "electricity", "sanitation", "roads", "streetlights", "other"}
    assert body["priority"] in {"high", "normal", "low"}
    assert body["triaged_by"] == "simulated"
    assert body["triage_latency_ms"] >= 0
    assert body["ai_summary"] is not None


@pytest.mark.asyncio
async def test_create_complaint_rejects_too_short_text(app_client):
    resp = await app_client.post(
        "/api/complaints", json={"text": "too short", "location": "Somewhere"}
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"] == "Validation failed"
    assert any(e["field"] == "text" for e in body["errors"])


@pytest.mark.asyncio
async def test_create_complaint_rejects_missing_location(app_client):
    resp = await app_client.post(
        "/api/complaints",
        json={"text": "A perfectly valid complaint body that is long enough to pass validation."},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_complaint_by_id_200(app_client, sample_complaint_payload):
    created = (await app_client.post("/api/complaints", json=sample_complaint_payload)).json()
    resp = await app_client.get(f"/api/complaints/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_complaint_by_id_404(app_client):
    resp = await app_client.get(f"/api/complaints/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_complaints_paginated(app_client, sample_complaint_payload):
    for _ in range(3):
        await app_client.post("/api/complaints", json=sample_complaint_payload)

    resp = await app_client.get("/api/complaints", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2


@pytest.mark.asyncio
async def test_list_complaints_filter_by_status(app_client, sample_complaint_payload):
    created = (await app_client.post("/api/complaints", json=sample_complaint_payload)).json()
    await app_client.patch(f"/api/complaints/{created['id']}/status", json={"status": "in_progress"})

    open_resp = await app_client.get("/api/complaints", params={"status": "open"})
    in_progress_resp = await app_client.get("/api/complaints", params={"status": "in_progress"})

    assert all(item["status"] == "open" for item in open_resp.json()["items"])
    assert any(item["id"] == created["id"] for item in in_progress_resp.json()["items"])
