import pytest


@pytest.mark.asyncio
async def test_stats_first_request_is_cache_miss(app_client):
    resp = await app_client.get("/api/stats")
    assert resp.status_code == 200
    assert resp.headers["X-Cache"] == "MISS"


@pytest.mark.asyncio
async def test_stats_second_request_is_cache_hit(app_client):
    first = await app_client.get("/api/stats")
    second = await app_client.get("/api/stats")

    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    # Cached payload should be identical to what was computed on the miss.
    assert first.json()["total"] == second.json()["total"]


@pytest.mark.asyncio
async def test_stats_cache_invalidated_on_new_complaint(app_client, sample_complaint_payload):
    # Warm the cache.
    warm = await app_client.get("/api/stats")
    assert warm.headers["X-Cache"] == "MISS"
    hit = await app_client.get("/api/stats")
    assert hit.headers["X-Cache"] == "HIT"
    assert hit.json()["total"] == 0

    # Writing a complaint must explicitly invalidate the cache, not wait for
    # the 30s TTL - the next stats read should be a MISS reflecting the new total.
    await app_client.post("/api/complaints", json=sample_complaint_payload)

    after_write = await app_client.get("/api/stats")
    assert after_write.headers["X-Cache"] == "MISS"
    assert after_write.json()["total"] == 1


@pytest.mark.asyncio
async def test_cache_provider_unit_get_set_delete(cache_provider):
    assert await cache_provider.get("k") is None
    await cache_provider.set("k", "v", ttl_seconds=30)
    assert await cache_provider.get("k") == "v"
    await cache_provider.delete("k")
    assert await cache_provider.get("k") is None
