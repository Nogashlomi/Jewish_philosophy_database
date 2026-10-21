import pytest
from app.core.db import db

@pytest.fixture
def captured_pipeline(monkeypatch):
    captured = {}
    results = [
        {"_id": "work_guide001", "label": "Guide of the Perplexed (Moreh Nevukhim)", "entity_type": "HistoricalWork", "_searchScore": 9.5},
        {"_id": "person_maimon01", "label": "Moses Maimonides (Rambam)", "entity_type": "HistoricalPerson", "_searchScore": 2.0},
    ]

    def aggregate(pipeline):
        captured["pipeline"] = pipeline
        return iter(results)

    monkeypatch.setattr(type(db.persons), "aggregate", lambda self, pipeline: aggregate(pipeline))
    return captured

def should_clauses(stage):
    return stage["$search"]["compound"]["should"]

@pytest.mark.asyncio
async def test_search_returns_mapped_results(async_client, captured_pipeline):
    response = await async_client.get("/api/v1/search/", params={"q": "Guide of the Perplexed"})
    assert response.status_code == 200
    assert response.json() == [
        {"id": "work_guide001", "label": "Guide of the Perplexed (Moreh Nevukhim)", "entity_type": "HistoricalWork", "score": 9.5},
        {"id": "person_maimon01", "label": "Moses Maimonides (Rambam)", "entity_type": "HistoricalPerson", "score": 2.0},
    ]

@pytest.mark.asyncio
async def test_search_boosts_phrase_and_matches_partial_words(async_client, captured_pipeline):
    await async_client.get("/api/v1/search/", params={"q": "Guide Perplexed"})
    should = should_clauses(captured_pipeline["pipeline"][0])
    assert should[0]["phrase"]["query"] == "Guide Perplexed"
    assert should[0]["phrase"]["score"]["boost"]["value"] > 1
    assert [c["wildcard"]["query"] for c in should if "wildcard" in c] == ["*guide*", "*perplexed*"]
    assert [c["text"]["query"] for c in should if "text" in c] == ["Guide", "Perplexed"]

@pytest.mark.asyncio
async def test_search_covers_all_collections_sorted_by_score(async_client, captured_pipeline):
    await async_client.get("/api/v1/search/", params={"q": "maimon", "limit": 5})
    pipeline = captured_pipeline["pipeline"]
    assert [stage["$unionWith"]["coll"] for stage in pipeline if "$unionWith" in stage] == ["works", "places"]
    assert pipeline[-2:] == [{"$sort": {"_searchScore": -1}}, {"$limit": 5}]

@pytest.mark.asyncio
@pytest.mark.parametrize("q, expected", [("*", "*\\**"), ("?", "*\\?*"), ("\\", "*\\\\*"), ("A*b?", "*a\\*b\\?*")])
async def test_search_escapes_wildcard_characters(async_client, captured_pipeline, q, expected):
    response = await async_client.get("/api/v1/search/", params={"q": q})
    assert response.status_code == 200
    wildcard = [c for c in should_clauses(captured_pipeline["pipeline"][0]) if "wildcard" in c]
    assert wildcard[0]["wildcard"]["query"] == expected

@pytest.mark.asyncio
async def test_search_requires_query(async_client):
    response = await async_client.get("/api/v1/search/", params={"q": ""})
    assert response.status_code == 422
