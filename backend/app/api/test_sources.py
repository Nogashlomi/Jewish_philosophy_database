import pytest

@pytest.mark.asyncio
async def test_read_sources(async_client, entity_id):
    response = await async_client.get("/api/v1/sources/")
    assert response.status_code == 200
    sources = response.json()
    ids = [source["id"] for source in sources]
    assert entity_id("sources", "Zonta Table") in ids
    assert len(ids) == len(set(ids))
    assert all(source["label"] and source["label"] != "None" for source in sources)

@pytest.mark.asyncio
async def test_source_mutations_require_token(async_client):
    body = {"name": "New"}
    assert (await async_client.post("/api/v1/sources/", json=body)).status_code == 401
    assert (await async_client.put("/api/v1/sources/source_unused01", json=body)).status_code == 401
    assert (await async_client.delete("/api/v1/sources/source_unused01")).status_code == 401

@pytest.mark.asyncio
async def test_source_mutations_reject_invalid_token(async_client):
    response = await async_client.delete("/api/v1/sources/source_unused01", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_source(async_client, auth_headers):
    response = await async_client.post(
        "/api/v1/sources/",
        json={"name": " New Source ", "shelfmark": "MS Heb 12", "url": "https://example.com/ms"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    created = response.json()
    assert created["id"].startswith("source_")
    assert created == {"id": created["id"], "label": "New Source", "shelfmark": "MS Heb 12", "url": "https://example.com/ms"}
    listed = next(s for s in (await async_client.get("/api/v1/sources/")).json() if s["id"] == created["id"])
    assert listed["shelfmark"] == "MS Heb 12"
    assert listed["url"] == "https://example.com/ms"

@pytest.mark.asyncio
async def test_create_source_with_name_only(async_client, auth_headers, seeded_db):
    response = await async_client.post("/api/v1/sources/", json={"name": "Bare", "shelfmark": " ", "url": ""}, headers=auth_headers)
    assert response.status_code == 201
    assert seeded_db.sources.find_one({"_id": response.json()["id"]}, {"_id": 0}) == {"name": "Bare"}

@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{"name": " "}, {"shelfmark": "MS 1"}, {"name": "X", "url": "example.com"}])
async def test_create_source_validates(async_client, auth_headers, body):
    response = await async_client.post("/api/v1/sources/", json=body, headers=auth_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_source_clears_missing_fields(async_client, auth_headers, seeded_db):
    response = await async_client.put("/api/v1/sources/source_unused01", json={"name": "Renamed", "url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"id": "source_unused01", "label": "Renamed", "shelfmark": None, "url": "https://example.com"}
    assert seeded_db.sources.find_one({"_id": "source_unused01"}, {"_id": 0}) == {"name": "Renamed", "url": "https://example.com"}

@pytest.mark.asyncio
async def test_update_source_not_found(async_client, auth_headers):
    response = await async_client.put("/api/v1/sources/source_zzzzzzzz", json={"name": "X"}, headers=auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_unlinked_source(async_client, auth_headers, seeded_db):
    response = await async_client.delete("/api/v1/sources/source_unused01", headers=auth_headers)
    assert response.status_code == 204
    assert seeded_db.sources.find_one({"_id": "source_unused01"}) is None

@pytest.mark.asyncio
async def test_delete_linked_source_fails(async_client, auth_headers, seeded_db):
    response = await async_client.delete("/api/v1/sources/source_zonta001", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Source is linked to 3 persons, 2 works, 1 places, 1 subjects"
    assert seeded_db.sources.find_one({"_id": "source_zonta001"}) is not None

@pytest.mark.asyncio
async def test_delete_source_cited_by_connection_fails(async_client, auth_headers, seeded_db):
    seeded_db.persons.update_one({"_id": "person_habill01"}, {"$set": {"times": [{"type": "activity", "from": 1470, "source": "source_unused01"}]}})
    response = await async_client.delete("/api/v1/sources/source_unused01", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Source is linked to 1 persons"

@pytest.mark.asyncio
async def test_delete_source_not_found(async_client, auth_headers):
    response = await async_client.delete("/api/v1/sources/source_zzzzzzzz", headers=auth_headers)
    assert response.status_code == 404
