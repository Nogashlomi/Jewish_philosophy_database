import re
import secrets
import string

from pymongo import ASCENDING
from pymongo.operations import SearchIndexModel
from pymongo.collation import Collation

ID_ALPHABET = string.ascii_lowercase + string.digits
ID_LENGTH = 8
NAME_COLLATION = Collation(locale="en", strength=1)

COLLECTION_PREFIXES = {
    "persons": "person",
    "works": "work",
    "places": "place",
    "subjects": "subject",
    "languages": "language",
    "sources": "source",
}
PREFIX_COLLECTIONS = {prefix: name for name, prefix in COLLECTION_PREFIXES.items()}


def new_id(prefix: str) -> str:
    return f"{prefix}_{''.join(secrets.choice(ID_ALPHABET) for _ in range(ID_LENGTH))}"


def id_prefix(entity_id: str) -> str:
    return entity_id.split("_", 1)[0]


def _ref(*prefixes: str) -> dict:
    group = prefixes[0] if len(prefixes) == 1 else f"({'|'.join(prefixes)})"
    return {"bsonType": "string", "pattern": f"^{group}_[a-z0-9]{{{ID_LENGTH}}}$"}


def _refs(*prefixes: str) -> dict:
    return {"bsonType": "array", "items": _ref(*prefixes)}


def ref_targets(pattern: str) -> list:
    match = re.match(r"^\^\(?([a-z|]+)\)?_", pattern)
    return [PREFIX_COLLECTIONS[prefix] for prefix in match.group(1).split("|")] if match else []


STRING = {"bsonType": "string"}
STRINGS = {"bsonType": "array", "items": STRING}
YEAR = {"bsonType": "int"}

COLLECTIONS = {
    "sources": {
        "bsonType": "object",
        "title": "Source",
        "description": "A scholarly project or data collection that provides information about persons and works.",
        "required": ["_id", "name"],
        "properties": {
            "_id": _ref("source"),
            "name": STRING,
            "url": STRING,
        },
    },
    "languages": {
        "bsonType": "object",
        "title": "Language",
        "description": "A historical or classical language used by persons or in works.",
        "required": ["_id", "name"],
        "properties": {
            "_id": _ref("language"),
            "name": STRING,
        },
    },
    "subjects": {
        "bsonType": "object",
        "title": "Subject",
        "description": "A topical subject area: astronomy, theology, philosophy, etc.",
        "required": ["_id", "name", "sources"],
        "properties": {
            "_id": _ref("subject"),
            "name": STRING,
            "description": STRING,
            "sources": _refs("source"),
        },
    },
    "places": {
        "bsonType": "object",
        "title": "Place",
        "description": "A geographic or historical location relevant to persons.",
        "required": ["_id", "name", "sources"],
        "properties": {
            "_id": _ref("place"),
            "name": STRING,
            "location": {
                "bsonType": "object",
                "required": ["type", "coordinates"],
                "properties": {
                    "type": {"enum": ["Point"]},
                    "coordinates": {"bsonType": "array", "minItems": 2, "maxItems": 2, "items": {"bsonType": "double"}},
                },
            },
            "sources": _refs("source"),
        },
    },
    "persons": {
        "bsonType": "object",
        "title": "Person",
        "description": "A historical person relevant to Jewish philosophy.",
        "required": ["_id", "name", "alt_names", "sources", "subjects", "languages", "times", "places", "relations"],
        "properties": {
            "_id": _ref("person"),
            "name": STRING,
            "alt_names": STRINGS,
            "name_verified": {"bsonType": "bool"},
            "viaf_id": STRING,
            "viaf_suggestions": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["viaf_id", "viaf_name", "name"],
                    "properties": {
                        "viaf_id": STRING,
                        "viaf_name": STRING,
                        "name": STRING,
                    },
                },
            },
            "description": STRING,
            "notes": STRINGS,
            "sources": _refs("source"),
            "subjects": _refs("subject"),
            "languages": _refs("language"),
            "times": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["type", "from"],
                    "properties": {
                        "type": STRING,
                        "from": YEAR,
                        "until": YEAR,
                        "label": STRING,
                    },
                },
            },
            "places": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["place", "type"],
                    "properties": {
                        "place": _ref("place"),
                        "type": STRING,
                        "from": YEAR,
                        "until": YEAR,
                        "time_label": STRING,
                        "description": STRING,
                    },
                },
            },
            "relations": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["type", "target"],
                    "properties": {
                        "type": {"enum": ["influenced_by", "cites", "interlocutor_of", "translated"]},
                        "target": _ref("person", "work"),
                    },
                },
            },
        },
    },
    "works": {
        "bsonType": "object",
        "title": "Work",
        "description": "A historical text authored or translated by historical persons.",
        "required": ["_id", "title", "sources", "subjects", "languages", "authors", "translators"],
        "properties": {
            "_id": _ref("work"),
            "title": STRING,
            "description": STRING,
            "authorship_status": STRING,
            "preservation_status": STRING,
            "sources": _refs("source"),
            "subjects": _refs("subject"),
            "languages": _refs("language"),
            "authors": _refs("person"),
            "translators": _refs("person"),
            "translation_of": _ref("work"),
        },
    },
}

INDEXES = {
    "sources": [("name", NAME_COLLATION)],
    "languages": [("name", NAME_COLLATION)],
    "subjects": [("name", NAME_COLLATION), ("sources", None)],
    "places": [("name", NAME_COLLATION), ("sources", None)],
    "persons": [
        ("name", NAME_COLLATION),
        ("alt_names", None),
        ("sources", None),
        ("subjects", None),
        ("languages", None),
        ("places.place", None),
        ("relations.target", None),
    ],
    "works": [
        ("title", NAME_COLLATION),
        ("sources", None),
        ("subjects", None),
        ("languages", None),
        ("authors", None),
        ("translators", None),
        ("translation_of", None),
    ],
}


SEARCH_INDEX_NAME = "text_search"
SEARCH_FIELDS = {
    "persons": ["name", "alt_names", "description", "notes"],
    "works": ["title", "description"],
    "places": ["name"],
}


def _search_definition(fields: list) -> dict:
    return {
        "mappings": {
            "dynamic": False,
            "fields": {field: {"type": "string", "analyzer": "lucene.standard"} for field in fields},
        }
    }


def ensure_schema(db) -> None:
    existing = set(db.list_collection_names())
    for name, schema in COLLECTIONS.items():
        validator = {"$jsonSchema": schema}
        if name in existing:
            db.command("collMod", name, validator=validator, validationLevel="strict", validationAction="error")
        else:
            db.create_collection(name, validator=validator, validationLevel="strict", validationAction="error")
        for field, collation in INDEXES[name]:
            options = {"collation": collation} if collation else {}
            db[name].create_index([(field, ASCENDING)], **options)
        if name in SEARCH_FIELDS:
            definition = _search_definition(SEARCH_FIELDS[name])
            existing_search = {index["name"]: index for index in db[name].list_search_indexes()}
            if SEARCH_INDEX_NAME not in existing_search:
                db[name].create_search_index(SearchIndexModel(definition=definition, name=SEARCH_INDEX_NAME))
            elif existing_search[SEARCH_INDEX_NAME].get("latestDefinition") != definition:
                db[name].update_search_index(SEARCH_INDEX_NAME, definition)
