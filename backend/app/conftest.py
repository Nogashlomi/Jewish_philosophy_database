import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.rdf_store import rdf_store
from app.core.config import settings

@pytest_asyncio.fixture
async def async_client():
    # Ensure data is loaded for tests
    if len(rdf_store.g) == 0:
        rdf_store.load_data()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
