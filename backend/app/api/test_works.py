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
    assert [author["id"] for author in data["authors"]] == ["Person_Moses_Maimonides_Rambam"]

@pytest.mark.asyncio
async def test_read_works_total_matches_items(async_client):
    response = await async_client.get("/api/v1/works/", params={"page_size": 500})
    data = response.json()
    assert data["total_pages"] == -(-data["total"] // 500)
    ids = [item["id"] for item in data["items"]]
    assert len(ids) == len(set(ids)) == 500

@pytest.mark.asyncio
async def test_read_work_not_found(async_client):
    response = await async_client.get("/api/v1/works/NonExistentID")
    assert response.status_code == 404
