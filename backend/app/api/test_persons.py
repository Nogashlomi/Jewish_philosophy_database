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
    person_id = entity_id("persons", "Moses Maimonides (Rambam)")
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
    person_id = entity_id("persons", "Moses Maimonides (Rambam)")
    response = await async_client.post(f"/api/v1/persons/{person_id}/name/verify", json={"viaf_id": "1"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_verify_name_rejects_invalid_token(async_client, entity_id):
    person_id = entity_id("persons", "Moses Maimonides (Rambam)")
    response = await async_client.post(
        f"/api/v1/persons/{person_id}/name/verify",
        json={"viaf_id": "1"},
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_verify_name(async_client, auth_headers):
    response = await async_client.post(
        "/api/v1/persons/person_menass01/name/verify",
        json={"name": "Menasseh ben Israel", "viaf_id": "123"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name_verified"] is True
    assert data["viaf_id"] == "123"

@pytest.mark.asyncio
async def test_person_detail_includes_connections(async_client):
    response = await async_client.get("/api/v1/persons/person_maimon01")
    assert response.status_code == 200
    assert response.json()["connections"] == [
        {"type": "lifespan", "place_id": None, "start": 1138, "end": 1204, "estimated": False, "description": None, "source_id": None, "place_label": None, "source_label": None},
        {"type": "birth", "place_id": "place_cordoba1", "start": 1138, "end": None, "estimated": False, "description": None, "source_id": None, "place_label": "Cordoba", "source_label": None},
        {"type": "residence", "place_id": "place_cairo001", "start": None, "end": None, "estimated": False, "description": "Court physician in Fustat.", "source_id": None, "place_label": "Cairo", "source_label": None},
    ]

@pytest.mark.asyncio
async def test_list_persons_formats_estimated_times(async_client):
    items = (await async_client.get("/api/v1/persons/", params={"search": "Tibbon"})).json()["items"]
    assert items[0]["times"] == "c. 1150–1230 (Lifespan)"

@pytest.mark.asyncio
async def test_update_connections(async_client, auth_headers, seeded_db):
    connections = [
        {"type": "birth", "place_id": "place_cordoba1", "start": 1136, "end": 1138, "estimated": True, "description": " Born here ", "source_id": "source_unused01"},
        {"type": "death", "start": 1204},
        {"type": "residence", "place_id": "place_cairo001"},
    ]
    response = await async_client.put("/api/v1/persons/person_maimon01/connections", json={"connections": connections}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    stored = seeded_db.persons.find_one({"_id": "person_maimon01"})
    assert stored["times"] == [{"type": "death", "from": 1204}]
    assert stored["places"] == [
        {"place": "place_cordoba1", "type": "birth", "from": 1136, "until": 1138, "estimated": True, "description": "Born here", "source": "source_unused01"},
        {"place": "place_cairo001", "type": "residence"},
    ]
    assert stored["sources"] == ["source_zonta001", "source_wiki0001", "source_unused01"]

    birth = next(c for c in data["connections"] if c["type"] == "birth")
    assert birth["source_label"] == "Unused Source"
    assert birth["place_label"] == "Cordoba"
    assert "1100-1149" in data["time_buckets"]
    assert any(p["source"] == "Unused Source" and p["estimated"] for p in data["places"])

@pytest.mark.asyncio
async def test_update_connections_drops_estimate_without_year(async_client, auth_headers, seeded_db):
    response = await async_client.put(
        "/api/v1/persons/person_maimon01/connections",
        json={"connections": [{"type": "residence", "place_id": "place_cairo001", "estimated": True}]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert seeded_db.persons.find_one({"_id": "person_maimon01"})["places"] == [{"place": "place_cairo001", "type": "residence"}]

@pytest.mark.asyncio
async def test_update_connections_requires_token(async_client):
    response = await async_client.put("/api/v1/persons/person_maimon01/connections", json={"connections": []})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_connections_rejects_invalid_token(async_client):
    response = await async_client.put(
        "/api/v1/persons/person_maimon01/connections",
        json={"connections": []},
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert response.status_code == 401

@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    {"type": "birth", "description": "Somewhere"},
    {"type": "lifespan", "start": 1204, "end": 1138},
    {"type": "lifespan", "end": 1204},
    {"type": "unknown", "start": 1138},
])
async def test_update_connections_validates_rows(async_client, auth_headers, connection):
    response = await async_client.put("/api/v1/persons/person_maimon01/connections", json={"connections": [connection]}, headers=auth_headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_connections_rejects_unknown_place(async_client, auth_headers, seeded_db):
    response = await async_client.put(
        "/api/v1/persons/person_maimon01/connections",
        json={"connections": [{"type": "birth", "place_id": "place_zzzzzzzz"}]},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "place_zzzzzzzz" in response.json()["detail"]
    assert len(seeded_db.persons.find_one({"_id": "person_maimon01"})["places"]) == 2

@pytest.mark.asyncio
async def test_update_connections_rejects_unknown_source(async_client, auth_headers):
    response = await async_client.put(
        "/api/v1/persons/person_maimon01/connections",
        json={"connections": [{"type": "birth", "start": 1138, "source_id": "source_zzzzzzzz"}]},
        headers=auth_headers,
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_connections_unknown_person(async_client, auth_headers):
    response = await async_client.put("/api/v1/persons/person_zzzzzzzz/connections", json={"connections": []}, headers=auth_headers)
    assert response.status_code == 404
