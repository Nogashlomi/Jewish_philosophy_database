import pytest

@pytest.mark.asyncio
async def test_read_network(async_client):
    response = await async_client.get("/api/v1/network/")
    assert response.status_code == 200
    data = response.json()
    ids = [node["id"] for node in data["nodes"]]
    assert len(ids) > 0
    assert len(ids) == len(set(ids))
    node_ids = set(ids)
    assert all(edge["from"] in node_ids and edge["to"] in node_ids for edge in data["edges"])
    assert any(node["buckets"] for node in data["nodes"] if node["group"] == "HistoricalPerson")

@pytest.mark.asyncio
async def test_read_network_source_filter(async_client):
    response = await async_client.get("/api/v1/network/", params={"source": "Source_Wikipedia"})
    assert response.status_code == 200
    data = response.json()
    ids = [node["id"] for node in data["nodes"]]
    assert len(ids) == len(set(ids))
    groups = {node["group"] for node in data["nodes"]}
    assert "HistoricalPerson" in groups
    assert "Place" in groups
    full = (await async_client.get("/api/v1/network/")).json()
    assert len(ids) < len(full["nodes"])

@pytest.mark.asyncio
async def test_read_network_unknown_source(async_client):
    response = await async_client.get("/api/v1/network/", params={"source": "Unknown>"})
    assert response.status_code == 200
    assert response.json() == {"nodes": [], "edges": []}
