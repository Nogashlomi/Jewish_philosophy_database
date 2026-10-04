import pytest

@pytest.mark.asyncio
async def test_read_subjects(async_client):
    response = await async_client.get("/api/v1/subjects/")
    assert response.status_code == 200
    subjects = response.json()
    assert len(subjects) > 0
    assert all(subject["label"] != "None" for subject in subjects)

@pytest.mark.asyncio
async def test_read_subject_detail_lists_only_works(async_client):
    response = await async_client.get("/api/v1/subjects/Subject_medicine")
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Medicine"
    ids = [work["id"] for work in data["works"]]
    assert len(ids) > 0
    assert len(ids) == len(set(ids))
    assert all(work_id.startswith("Work_") for work_id in ids)

@pytest.mark.asyncio
async def test_read_subject_not_found(async_client):
    response = await async_client.get("/api/v1/subjects/NonExistentID")
    assert response.status_code == 404
