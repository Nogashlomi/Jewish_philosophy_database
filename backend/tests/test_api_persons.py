import pytest

@pytest.mark.asyncio
async def test_read_persons(async_client):
    response = await async_client.get("/api/v1/persons/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["total"] > 0

@pytest.mark.asyncio
async def test_read_person_detail(async_client):
    # Test with a known ID from the sample data
    response = await async_client.get("/api/v1/persons/Person_Maimonides")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "Person_Maimonides"
    assert "Maimon" in data["label"] or "Rambam" in data["label"]

@pytest.mark.asyncio
async def test_read_person_not_found(async_client):
    response = await async_client.get("/api/v1/persons/NonExistentID")
    assert response.status_code == 404
