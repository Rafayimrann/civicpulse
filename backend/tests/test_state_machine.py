import pytest

from app.models import Status
from app.services.state_machine import InvalidTransitionError, validate_transition


# --- Pure unit tests of the transition table itself ---

def test_open_to_in_progress_is_valid():
    validate_transition(Status.open, Status.in_progress)  # should not raise


def test_open_to_rejected_is_valid():
    validate_transition(Status.open, Status.rejected)


def test_in_progress_to_resolved_is_valid():
    validate_transition(Status.in_progress, Status.resolved)


def test_open_to_resolved_is_invalid():
    with pytest.raises(InvalidTransitionError):
        validate_transition(Status.open, Status.resolved)


def test_resolved_is_terminal():
    with pytest.raises(InvalidTransitionError):
        validate_transition(Status.resolved, Status.open)


def test_rejected_is_terminal():
    with pytest.raises(InvalidTransitionError):
        validate_transition(Status.rejected, Status.in_progress)


# --- End-to-end through the API, asserting the 409 contract ---


@pytest.mark.asyncio
async def test_valid_transition_via_api_returns_200(app_client, sample_complaint_payload):
    created = (await app_client.post("/api/complaints", json=sample_complaint_payload)).json()

    resp = await app_client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "in_progress"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_invalid_transition_via_api_returns_409_with_message(app_client, sample_complaint_payload):
    created = (await app_client.post("/api/complaints", json=sample_complaint_payload)).json()

    # open -> resolved directly is not allowed; must go through in_progress.
    resp = await app_client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "resolved"}
    )
    assert resp.status_code == 409
    body = resp.json()
    assert "open" in body["detail"]
    assert "resolved" in body["detail"]


@pytest.mark.asyncio
async def test_transition_on_terminal_status_returns_409(app_client, sample_complaint_payload):
    created = (await app_client.post("/api/complaints", json=sample_complaint_payload)).json()
    await app_client.patch(f"/api/complaints/{created['id']}/status", json={"status": "in_progress"})
    await app_client.patch(f"/api/complaints/{created['id']}/status", json={"status": "resolved"})

    resp = await app_client.patch(
        f"/api/complaints/{created['id']}/status", json={"status": "in_progress"}
    )
    assert resp.status_code == 409
