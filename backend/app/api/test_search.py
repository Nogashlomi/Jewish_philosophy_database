import pytest

@pytest.mark.asyncio
async def test_search_is_case_insensitive(async_client):
    lower = (await async_client.get("/api/v1/search/", params={"q": "maimonides"})).json()
    upper = (await async_client.get("/api/v1/search/", params={"q": "MAIMONIDES"})).json()
    assert len(lower) > 0
    assert [r["id"] for r in lower] == [r["id"] for r in upper]

@pytest.mark.asyncio
async def test_search_matches_partial_words(async_client):
    results = (await async_client.get("/api/v1/search/", params={"q": "maimon"})).json()
    assert any("maimon" in r["label"].lower() for r in results)

@pytest.mark.asyncio
async def test_search_ranks_phrase_first(async_client):
    results = (await async_client.get("/api/v1/search/", params={"q": "Guide of the Perplexed"})).json()
    assert "guide of the perplexed" in results[0]["label"].lower()
    assert results == sorted(results, key=lambda r: -r["score"])

@pytest.mark.asyncio
@pytest.mark.parametrize("q", ["*", "?", "\\", "a*b?"])
async def test_search_special_characters(async_client, q):
    response = await async_client.get("/api/v1/search/", params={"q": q})
    assert response.status_code == 200
