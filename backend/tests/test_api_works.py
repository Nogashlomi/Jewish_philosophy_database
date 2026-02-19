import pytest

@pytest.mark.asyncio
async def test_read_works(async_client):
    response = await async_client.get("/api/v1/works/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_work_detail(async_client):
    # Test with a known ID from the sample data
    # Assuming W_013 is Guide of the Perplexed based on previous file reads
    response = await async_client.get("/api/v1/works/W_013")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "W_013"
    assert "Guide" in data["title"]
