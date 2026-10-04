import pytest

@pytest.mark.asyncio
async def test_read_geojson(async_client):
    response = await async_client.get("/api/v1/geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    lon, lat = data["features"][0]["geometry"]["coordinates"]
    assert -180 <= lon <= 180 and -90 <= lat <= 90

@pytest.mark.asyncio
async def test_read_geojson_source_filter(async_client):
    full = (await async_client.get("/api/v1/geojson")).json()
    filtered = (await async_client.get("/api/v1/geojson", params={"source": "Source_Zonta"})).json()
    assert 0 < len(filtered["features"]) < len(full["features"])
