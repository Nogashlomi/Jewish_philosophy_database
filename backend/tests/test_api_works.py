import pytest

@pytest.mark.asyncio
async def test_read_works(async_client):
    response = await async_client.get("/api/v1/works/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["total"] > 0

@pytest.mark.asyncio
async def test_read_work_detail(async_client):
    # Test with a known ID from the sample data
    response = await async_client.get("/api/v1/works/Work_Guide_of_the_Perplexed_Moreh_Nevukhim")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "Work_Guide_of_the_Perplexed_Moreh_Nevukhim"
    assert "Guide" in data["title"]
