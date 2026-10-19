import pytest

@pytest.mark.asyncio
async def test_read_persons(async_client):
    response = await async_client.get("/api/v1/persons/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert data["total"] > 0

@pytest.mark.asyncio
async def test_read_person_detail(async_client, entity_id):
    person_id = entity_id("persons", "Maimonides")
    assert person_id.startswith("person_")
    response = await async_client.get(f"/api/v1/persons/{person_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == person_id
    assert "Maimon" in data["label"] or "Rambam" in data["label"]

@pytest.mark.asyncio
async def test_read_person_not_found(async_client):
    response = await async_client.get("/api/v1/persons/NonExistentID")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_read_persons_has_no_duplicates_for_multi_label_persons(async_client, entity_id):
    response = await async_client.get("/api/v1/persons/", params={"page_size": 500})
    data = response.json()
    ids = [item["id"] for item in data["items"]]
    while data["page"] < data["total_pages"]:
        response = await async_client.get("/api/v1/persons/", params={"page_size": 500, "page": data["page"] + 1})
        data = response.json()
        ids += [item["id"] for item in data["items"]]
    assert len(ids) == len(set(ids)) == data["total"]
    assert ids.count(entity_id("persons", "Eli Habillo")) == 1

@pytest.mark.asyncio
async def test_read_persons_source_filter(async_client, entity_id):
    all_persons = (await async_client.get("/api/v1/persons/")).json()
    filtered = (await async_client.get("/api/v1/persons/", params={"source": entity_id("sources", "Wikipedia")})).json()
    assert 0 < filtered["total"] < all_persons["total"]

@pytest.mark.asyncio
async def test_read_persons_unknown_source_is_empty(async_client):
    response = await async_client.get("/api/v1/persons/", params={"source": "x> . ?s ?p ?o"})
    assert response.status_code == 200
    assert response.json()["total"] == 0

@pytest.mark.asyncio
async def test_read_persons_search(async_client):
    response = await async_client.get("/api/v1/persons/", params={"search": "MAIMON"})
    data = response.json()
    assert data["total"] > 0
    assert all("maimon" in item["label"].lower() for item in data["items"])

@pytest.mark.asyncio
@pytest.mark.parametrize("search", ["\\", '"', "a\") || true || (\"", "line\nbreak"])
async def test_read_persons_search_special_characters(async_client, search):
    response = await async_client.get("/api/v1/persons/", params={"search": search})
    assert response.status_code == 200
    assert response.json()["total"] == 0

@pytest.mark.asyncio
async def test_read_person_detail_related_data(async_client, entity_id):
    response = await async_client.get(f"/api/v1/persons/{entity_id('persons', 'Menasseh ben Israel')}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["works"]) > 0
    assert all(work["title"] for work in data["works"])
    assert "Hebrew" in data["languages"]
    assert "1600-1649" in data["time_buckets"]
    assert len(data["time_buckets"]) == len(set(data["time_buckets"]))

@pytest.mark.asyncio
async def test_verify_name_requires_token(async_client, entity_id):
    person_id = entity_id("persons", "Maimonides")
    response = await async_client.post(f"/api/v1/persons/{person_id}/name/verify", json={"viaf_id": "1"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_verify_name_rejects_invalid_token(async_client, entity_id):
    person_id = entity_id("persons", "Maimonides")
    response = await async_client.post(
        f"/api/v1/persons/{person_id}/name/verify",
        json={"viaf_id": "1"},
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert response.status_code == 401
