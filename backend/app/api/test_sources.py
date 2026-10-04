import pytest

@pytest.mark.asyncio
async def test_read_sources(async_client):
    response = await async_client.get("/api/v1/sources/")
    assert response.status_code == 200
    sources = response.json()
    ids = [source["id"] for source in sources]
    assert "Source_Zonta" in ids
    assert len(ids) == len(set(ids))
    assert all(source["label"] and source["label"] != "None" for source in sources)
