import pytest

@pytest.mark.asyncio
async def test_read_places(async_client):
    response = await async_client.get("/api/v1/places/")
    assert response.status_code == 200
    ids = [place["id"] for place in response.json()]
    assert len(ids) > 0
    assert len(ids) == len(set(ids))

@pytest.mark.asyncio
async def test_read_place_detail(async_client):
    response = await async_client.get("/api/v1/places/Place_Cairo")
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Cairo"
    assert len(data["people"]) > 0
    keys = [(person["id"], person["type"]) for person in data["people"]]
    assert len(keys) == len(set(keys))

@pytest.mark.asyncio
async def test_read_place_not_found(async_client):
    response = await async_client.get("/api/v1/places/NonExistentID")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_read_places_geojson(async_client):
    response = await async_client.get("/api/v1/places/geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

@pytest.mark.asyncio
async def test_read_translation_flows(async_client):
    response = await async_client.get("/api/v1/places/translations/flows")
    assert response.status_code == 200
    flows = response.json()
    assert len(flows) > 0
    keys = [(f["translator_id"], f["author_id"], tuple(map(tuple, f["path"]))) for f in flows]
    assert len(keys) == len(set(keys))
    assert all(len(f["path"]) == 2 for f in flows)
