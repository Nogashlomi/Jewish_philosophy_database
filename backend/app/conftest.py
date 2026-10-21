import os

import mongomock
import pymongo
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
pymongo.MongoClient = mongomock.MongoClient
mongomock.collection.Cursor.collation = lambda self, collation=None: self

from app.main import app
from app.core import auth
from app.core.config import settings
from app.core.db import db

VALID_TOKEN = "valid-token"
AUTH_HEADERS = {"Authorization": f"Bearer {VALID_TOKEN}"}

SEED = {
    "sources": [
        {"_id": "source_zonta001", "name": "Zonta Table"},
        {"_id": "source_wiki0001", "name": "Wikipedia", "url": "https://en.wikipedia.org"},
        {"_id": "source_unused01", "name": "Unused Source", "shelfmark": "MS 1"},
    ],
    "languages": [
        {"_id": "language_arabic01", "name": "Arabic"},
        {"_id": "language_hebrew01", "name": "Hebrew"},
        {"_id": "language_latin001", "name": "Latin"},
    ],
    "subjects": [
        {"_id": "subject_medicin1", "name": "Medicine", "sources": ["source_zonta001"]},
        {"_id": "subject_philoso1", "name": "Philosophy", "sources": ["source_wiki0001"]},
    ],
    "places": [
        {"_id": "place_cairo001", "name": "Cairo", "sources": ["source_zonta001"], "location": {"type": "Point", "coordinates": [31.2357, 30.0444]}},
        {"_id": "place_cordoba1", "name": "Cordoba", "sources": ["source_wiki0001"], "location": {"type": "Point", "coordinates": [-4.7794, 37.8882]}},
        {"_id": "place_amsterd1", "name": "Amsterdam", "sources": ["source_wiki0001"], "location": {"type": "Point", "coordinates": [4.9041, 52.3676]}},
        {"_id": "place_marsei01", "name": "Marseille", "sources": [], "location": {"type": "Point", "coordinates": [5.3698, 43.2965]}},
        {"_id": "place_toledo01", "name": "Toledo", "sources": []},
    ],
    "persons": [
        {
            "_id": "person_maimon01",
            "name": "Moses Maimonides (Rambam)",
            "alt_names": ["Maimonides", "Rambam"],
            "sources": ["source_zonta001", "source_wiki0001"],
            "subjects": ["subject_medicin1", "subject_philoso1"],
            "languages": ["language_arabic01", "language_hebrew01"],
            "times": [{"type": "lifespan", "from": 1138, "until": 1204}],
            "places": [
                {"place": "place_cordoba1", "type": "birth", "from": 1138},
                {"place": "place_cairo001", "type": "residence", "description": "Court physician in Fustat."},
            ],
            "relations": [],
        },
        {
            "_id": "person_menass01",
            "name": "Menasseh ben Israel",
            "alt_names": [],
            "sources": ["source_wiki0001"],
            "subjects": ["subject_philoso1"],
            "languages": ["language_hebrew01", "language_latin001"],
            "times": [{"type": "lifespan", "from": 1604, "until": 1657}],
            "places": [{"place": "place_amsterd1", "type": "residence"}],
            "relations": [
                {"type": "influenced_by", "target": "person_maimon01"},
                {"type": "cites", "target": "work_guide001"},
            ],
        },
        {
            "_id": "person_habill01",
            "name": "Eli Habillo",
            "alt_names": ["Elijah Habillo", "Eli Habilio"],
            "sources": ["source_zonta001"],
            "subjects": [],
            "languages": ["language_hebrew01", "language_latin001"],
            "times": [{"type": "activity", "from": 1470, "estimated": True}],
            "places": [],
            "relations": [],
        },
        {
            "_id": "person_tibbon01",
            "name": "Samuel ibn Tibbon",
            "alt_names": [],
            "sources": ["source_zonta001"],
            "subjects": ["subject_philoso1"],
            "languages": ["language_hebrew01", "language_arabic01"],
            "times": [{"type": "lifespan", "from": 1150, "until": 1230, "estimated": True}],
            "places": [{"place": "place_marsei01", "type": "death", "from": 1230, "estimated": True}],
            "relations": [],
        },
        {
            "_id": "person_ibnrus01",
            "name": "Averroes",
            "alt_names": ["Ibn Rushd"],
            "sources": ["source_wiki0001"],
            "subjects": ["subject_medicin1"],
            "languages": ["language_arabic01"],
            "times": [{"type": "lifespan", "from": 1126, "until": 1198}],
            "places": [{"place": "place_cordoba1", "type": "birth"}, {"place": "place_toledo01", "type": "travel"}],
            "relations": [],
        },
    ],
    "works": [
        {
            "_id": "work_guide001",
            "title": "Guide of the Perplexed (Moreh Nevukhim)",
            "sources": ["source_zonta001", "source_wiki0001"],
            "subjects": ["subject_philoso1"],
            "languages": ["language_arabic01"],
            "authors": ["person_maimon01"],
            "translators": [],
        },
        {
            "_id": "work_guidehe1",
            "title": "Moreh Nevukhim (Hebrew translation)",
            "sources": ["source_zonta001"],
            "subjects": ["subject_philoso1"],
            "languages": ["language_hebrew01"],
            "authors": [],
            "translators": ["person_tibbon01"],
            "translation_of": "work_guide001",
        },
        {
            "_id": "work_aphori01",
            "title": "Medical Aphorisms",
            "sources": ["source_wiki0001"],
            "subjects": ["subject_medicin1"],
            "languages": ["language_arabic01"],
            "authors": ["person_maimon01"],
            "translators": [],
        },
        {
            "_id": "work_nishma01",
            "title": "Nishmat Hayyim",
            "sources": ["source_wiki0001"],
            "subjects": ["subject_philoso1"],
            "languages": ["language_hebrew01"],
            "authors": ["person_menass01"],
            "translators": [],
        },
    ],
}


def fake_verify_firebase_token(token, request, audience=None):
    if token != VALID_TOKEN:
        raise ValueError("Invalid token")
    return {"iss": f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}", "sub": "test-user", "email": "test@example.com"}


@pytest.fixture(autouse=True)
def seeded_db(monkeypatch):
    monkeypatch.setattr(auth.id_token, "verify_firebase_token", fake_verify_firebase_token)
    for name in db.list_collection_names():
        db.drop_collection(name)
    for name, docs in SEED.items():
        db[name].insert_many([dict(doc) for doc in docs])
    yield db


@pytest.fixture
def entity_id():
    def find(collection, name):
        field = "title" if collection == "works" else "name"
        return db[collection].find_one({field: name}, {"_id": 1})["_id"]
    return find


@pytest.fixture
def auth_headers():
    return AUTH_HEADERS


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
