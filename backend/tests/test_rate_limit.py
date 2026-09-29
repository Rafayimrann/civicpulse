import pytest

from tests.conftest import RATE_LIMIT_MAX


@pytest.mark.asyncio
async def test_rate_limit_allows_requests_under_the_limit(app_client, sample_complaint_payload):
    for _ in range(RATE_LIMIT_MAX):
        resp = await app_client.post("/api/complaints", json=sample_complaint_payload)
        assert resp.status_code == 201


@pytest.mark.asyncio
async def test_rate_limit_returns_429_with_retry_after_when_exceeded(app_client, sample_complaint_payload):
    for _ in range(RATE_LIMIT_MAX):
        resp = await app_client.post("/api/complaints", json=sample_complaint_payload)
        assert resp.status_code == 201

    over_limit_resp = await app_client.post("/api/complaints", json=sample_complaint_payload)

    assert over_limit_resp.status_code == 429
    assert "Retry-After" in over_limit_resp.headers
    assert int(over_limit_resp.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_rate_limiter_unit_fixed_window(rate_limiter):
    identifier = "1.2.3.4"
    for _ in range(5):
        result = await rate_limiter.check(identifier)
        assert result.allowed is True

    blocked = await rate_limiter.check(identifier)
    assert blocked.allowed is False
    assert blocked.remaining == 0
    assert blocked.retry_after_seconds > 0
