import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import db

@pytest.fixture
def entity_id():
    def find(collection, name):
        field = "title" if collection == "works" else "name"
        return db[collection].find_one({field: name}, {"_id": 1})["_id"]
    return find

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
