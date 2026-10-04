import pytest

@pytest.mark.asyncio
async def test_read_languages(async_client):
    response = await async_client.get("/api/v1/languages/")
    assert response.status_code == 200
    ids = [language["id"] for language in response.json()]
    assert "Language_Arabic" in ids
    assert len(ids) == len(set(ids))

@pytest.mark.asyncio
async def test_read_language_detail(async_client):
    response = await async_client.get("/api/v1/languages/Language_Arabic")
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Arabic"
    ids = [person["id"] for person in data["persons"]]
    assert len(ids) > 0
    assert len(ids) == len(set(ids))

@pytest.mark.asyncio
async def test_read_language_not_found(async_client):
    response = await async_client.get("/api/v1/languages/NonExistentID")
    assert response.status_code == 404
