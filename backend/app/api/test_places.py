import pytest

@pytest.mark.asyncio
async def test_read_places(async_client):
    response = await async_client.get("/api/v1/places/")
    assert response.status_code == 200
    ids = [place["id"] for place in response.json()]
    assert len(ids) > 0
    assert len(ids) == len(set(ids))

@pytest.mark.asyncio
async def test_read_place_detail(async_client, entity_id):
    response = await async_client.get(f"/api/v1/places/{entity_id('places', 'Cairo')}")
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

@pytest.mark.asyncio
async def test_create_place_requires_token(async_client):
    response = await async_client.post("/api/v1/places/", json={"name": "Nowhere", "lat": 1, "long": 1})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_place(async_client, auth_headers, seeded_db):
    response = await async_client.post("/api/v1/places/", json={"name": " Fez ", "lat": 34.0181, "long": -5.0078}, headers=auth_headers)
    assert response.status_code == 201
    created = response.json()
    assert created == {"id": created["id"], "label": "Fez", "lat": "34.0181", "long": "-5.0078", "personCount": 0}
    assert seeded_db.places.find_one({"_id": created["id"]}, {"_id": 0}) == {
        "name": "Fez",
        "sources": [],
        "location": {"type": "Point", "coordinates": [-5.0078, 34.0181]},
    }

@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{"name": "X", "lat": 91, "long": 0}, {"name": "X", "lat": 0, "long": 181}, {"name": " ", "lat": 0, "long": 0}, {"name": "X", "lat": 0}])
async def test_create_place_validates(async_client, auth_headers, body):
    response = await async_client.post("/api/v1/places/", json=body, headers=auth_headers)
    assert response.status_code == 422
