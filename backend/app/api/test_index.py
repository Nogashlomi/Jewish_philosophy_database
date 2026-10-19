import pytest

@pytest.mark.asyncio
async def test_read_stats(async_client):
    response = await async_client.get("/api/v1/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["persons"] > 0
    assert stats["works"] > 0

@pytest.mark.asyncio
async def test_read_stats_source_filter(async_client, entity_id):
    full = (await async_client.get("/api/v1/stats")).json()
    filtered = (await async_client.get("/api/v1/stats", params={"source": entity_id("sources", "Zonta Table")})).json()
    assert 0 < filtered["persons"] < full["persons"]
    assert 0 < filtered["works"] < full["works"]

@pytest.mark.asyncio
async def test_read_stats_invalid_source(async_client):
    response = await async_client.get("/api/v1/stats", params={"source": "x> . ?s ?p ?o"})
    assert response.status_code == 200
    stats = response.json()
    assert stats["persons"] == 0
    assert stats["works"] == 0
