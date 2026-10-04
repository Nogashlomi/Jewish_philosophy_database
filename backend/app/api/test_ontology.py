import pytest

@pytest.mark.asyncio
async def test_read_ontology(async_client):
    response = await async_client.get("/api/v1/ontology/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0

@pytest.mark.asyncio
async def test_read_ontology_audit(async_client):
    response = await async_client.get("/api/v1/ontology/audit")
    assert response.status_code == 200
    data = response.json()
    assert data["classes"]["defined_count"] > 0
    assert data["properties"]["defined_count"] > 0
