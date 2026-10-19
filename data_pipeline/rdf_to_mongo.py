import argparse
import os
import re
import sys
from pathlib import Path

from pymongo import MongoClient
from rdflib import Graph, Namespace, RDF, RDFS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.db_schema import COLLECTIONS, COLLECTION_PREFIXES, ID_LENGTH, ensure_schema, new_id

JP = Namespace("http://jewish_philosophy.org/ontology#")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
SCHEMA = Namespace("http://schema.org/")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_NAME = "jephy"
DELMEDIGO = JP.Person_Joseph_Solomon_Delmedigo
SUBJECT_ALIASES = {"grammer": "grammar"}
RELATION_PREDICATES = {"influenced_by": JP.influencedBy, "cites": JP.cites, "interlocutor_of": JP.interlocutorOf}
ID_PATTERN = re.compile(rf"^({'|'.join(COLLECTION_PREFIXES.values())})_[a-z0-9]{{{ID_LENGTH}}}$")
CLASSES = {
    "sources": JP.Source,
    "languages": JP.Language,
    "subjects": JP.Subject,
    "places": JP.Place,
    "persons": JP.HistoricalPerson,
    "works": JP.HistoricalWork,
}


def load_graph() -> Graph:
    g = Graph()
    for path in sorted(DATA_DIR.rglob("*.ttl")):
        g.parse(str(path), format="turtle")
    return g


def local_name(uri) -> str:
    return str(uri).split("#")[-1]


def pick_label(labels) -> str:
    return min(labels, key=lambda l: (l.count("(") != l.count(")"), l.endswith("?"), "." in l, l))


def unique(values) -> list:
    return list(dict.fromkeys(values))


class Migration:
    def __init__(self, g: Graph):
        self.g = g
        self.ids = {}
        self.groups = {}
        self.warnings = []

    def labels(self, uris) -> list:
        return unique(str(l).strip() for u in uris for l in self.g.objects(u, RDFS.label) if str(l).strip())

    def first(self, uris, predicate):
        for u in uris:
            value = self.g.value(u, predicate)
            if value is not None:
                return value
        return None

    def strings(self, uris, predicate) -> list:
        return unique(str(o).strip() for u in uris for o in self.g.objects(u, predicate) if str(o).strip())

    def refs(self, uris, predicate) -> list:
        result = []
        for u in uris:
            for o in self.g.objects(u, predicate):
                if o in self.ids:
                    result.append(self.ids[o])
                else:
                    self.warnings.append(f"dangling {local_name(predicate)} from {local_name(u)} to {local_name(o)}")
        return unique(result)

    def entity_uris(self, collection: str) -> list:
        uris = set(self.g.subjects(RDF.type, CLASSES[collection]))
        if collection == "sources":
            uris |= set(self.g.objects(None, JP.hasSource))
        return sorted(uris, key=str)

    def group_key(self, collection: str, uri):
        if collection in ("works", "sources"):
            return uri
        labels = self.labels([uri])
        if not labels:
            return uri
        key = pick_label(labels).lower()
        return SUBJECT_ALIASES.get(key, key) if collection == "subjects" else key

    def assign_ids(self):
        used = set()
        for collection in CLASSES:
            groups = {}
            for uri in self.entity_uris(collection):
                groups.setdefault(self.group_key(collection, uri), []).append(uri)
            self.groups[collection] = {}
            for uris in groups.values():
                entity_id = new_id(COLLECTION_PREFIXES[collection])
                while entity_id in used:
                    entity_id = new_id(COLLECTION_PREFIXES[collection])
                used.add(entity_id)
                self.groups[collection][entity_id] = uris
                for uri in uris:
                    self.ids[uri] = entity_id
                if len(uris) > 1:
                    self.warnings.append(f"merged {collection}: {', '.join(local_name(u) for u in uris)}")

    def name(self, uris) -> str:
        labels = self.labels(uris)
        return pick_label(labels) if labels else local_name(uris[0]).split("_", 1)[-1].replace("_", " ")

    def year(self, value):
        return int(str(value)) if value is not None else None

    def time_fields(self, time_data, from_key: str, until_key: str, label_key: str) -> dict:
        if time_data is None:
            return {}
        fields = {
            from_key: self.year(self.g.value(time_data, JP.timeFrom)),
            until_key: self.year(self.g.value(time_data, JP.timeUntil)),
            label_key: self.g.value(time_data, JP.timeLabel),
        }
        return {k: (str(v) if k == label_key else v) for k, v in fields.items() if v is not None}

    def build_sources(self, entity_id, uris) -> dict:
        doc = {"_id": entity_id, "name": self.name(uris)}
        url = self.first(uris, SCHEMA.url)
        if url is not None:
            doc["url"] = str(url)
        return doc

    def build_languages(self, entity_id, uris) -> dict:
        return {"_id": entity_id, "name": self.name(uris)}

    def build_subjects(self, entity_id, uris) -> dict:
        doc = {"_id": entity_id, "name": self.name(uris), "sources": self.refs(uris, JP.hasSource)}
        description = self.first(uris, JP.hasDescription)
        if description is not None:
            doc["description"] = str(description)
        return doc

    def build_places(self, entity_id, uris) -> dict:
        doc = {"_id": entity_id, "name": self.name(uris), "sources": self.refs(uris, JP.hasSource)}
        for lat_predicate, long_predicate in ((JP.latitude, JP.longitude), (GEO.lat, GEO.long)):
            lat = self.first(uris, lat_predicate)
            long = self.first(uris, long_predicate)
            if lat is not None and long is not None:
                doc["location"] = {"type": "Point", "coordinates": [float(long), float(lat)]}
                break
        return doc

    def build_persons(self, entity_id, uris) -> dict:
        name = self.name(uris)
        doc = {
            "_id": entity_id,
            "name": name,
            "alt_names": [l for l in self.labels(uris) if l != name],
            "sources": self.refs(uris, JP.hasSource),
            "subjects": unique(self.refs(uris, JP.hasSubject) + [
                self.ids[s] for u in uris for s in self.g.subjects(JP.isSubjectOf, u) if s in self.ids
            ]),
            "languages": self.refs(uris, JP.hasLanguage),
            "times": [],
            "places": [],
            "relations": [],
        }
        description = self.first(uris, SCHEMA.description)
        if description is not None:
            doc["description"] = str(description)
        notes = self.strings(uris, JP.hasRelation)
        if notes:
            doc["notes"] = notes

        for u in uris:
            for tr in self.g.objects(u, JP.hasTimeRelation):
                time = {"type": str(self.g.value(tr, JP.timeType) or "lifespan")}
                time.update(self.time_fields(self.g.value(tr, JP.hasTimeData), "from", "until", "label"))
                if "from" in time and time not in doc["times"]:
                    doc["times"].append(time)

            for pr in self.g.objects(u, JP.hasPlaceRelation):
                place = self.g.value(pr, JP.relatedPlace)
                if place not in self.ids:
                    self.warnings.append(f"dangling place relation {local_name(pr)}")
                    continue
                rel = {"place": self.ids[place], "type": str(self.g.value(pr, JP.placeType) or "associated")}
                rel.update(self.time_fields(self.g.value(pr, JP.hasTimeData), "from", "until", "time_label"))
                description = self.g.value(pr, SCHEMA.description)
                if description is None and u == DELMEDIGO:
                    description = self.g.value(place, JP.hasRelation)
                if description is not None:
                    rel["description"] = str(description)
                if rel not in doc["places"]:
                    doc["places"].append(rel)

        doc["times"].sort(key=lambda t: t["from"])
        doc["places"].sort(key=lambda p: (p.get("from") is None, p.get("from", 0)))

        for relation, predicate in RELATION_PREDICATES.items():
            doc["relations"] += [{"type": relation, "target": target} for target in self.refs(uris, predicate)]
        return doc

    def build_works(self, entity_id, uris) -> dict:
        doc = {
            "_id": entity_id,
            "title": self.name(uris),
            "sources": self.refs(uris, JP.hasSource),
            "subjects": self.refs(uris, JP.hasSubject),
            "languages": self.refs(uris, JP.hasLanguage),
            "authors": self.refs(uris, JP.writtenBy),
            "translators": self.refs(uris, JP.translatedBy),
        }
        for key, predicate in (
            ("description", SCHEMA.description),
            ("authorship_status", JP.authorshipStatus),
            ("preservation_status", JP.preservationStatus),
        ):
            value = self.first(uris, predicate)
            if value is not None:
                doc[key] = str(value)
        translation_of = self.refs(uris, JP.isTranslationOf)
        if translation_of:
            doc["translation_of"] = translation_of[0]
        return doc

    def add_explicit_translations(self, documents: dict):
        works = {w["_id"]: w for w in documents["works"]}
        derived = {
            (translator, author)
            for w in works.values() if w.get("translation_of") in works
            for translator in w["translators"]
            for author in works[w["translation_of"]]["authors"]
        }
        persons = {p["_id"]: p for p in documents["persons"]}
        for translator_uri, author_uri in self.g.subject_objects(JP.translated):
            pair = (self.ids.get(translator_uri), self.ids.get(author_uri))
            if None in pair or pair in derived:
                continue
            relation = {"type": "translated", "target": pair[1]}
            if relation not in persons[pair[0]]["relations"]:
                persons[pair[0]]["relations"].append(relation)

    def check_references(self, documents: dict):
        existing = {doc["_id"] for docs in documents.values() for doc in docs}

        def walk(value, path):
            if isinstance(value, dict):
                for k, v in value.items():
                    if k != "_id":
                        yield from walk(v, f"{path}.{k}")
            elif isinstance(value, list):
                for v in value:
                    yield from walk(v, path)
            elif isinstance(value, str) and ID_PATTERN.match(value):
                yield path, value

        for collection, docs in documents.items():
            for doc in docs:
                for path, ref in walk(doc, collection):
                    if ref not in existing:
                        self.warnings.append(f"missing reference {path} -> {ref} in {doc['_id']}")

    def build(self) -> dict:
        self.assign_ids()
        documents = {
            collection: [getattr(self, f"build_{collection}")(entity_id, uris) for entity_id, uris in self.groups[collection].items()]
            for collection in CLASSES
        }
        self.add_explicit_translations(documents)
        self.check_references(documents)
        return documents


def main():
    parser = argparse.ArgumentParser(description="Migrate the RDF data files into the jephy MongoDB database.")
    parser.add_argument("--drop", action="store_true", help="Drop existing collections before loading")
    parser.add_argument("--dry-run", action="store_true", help="Build documents and report without writing to MongoDB")
    args = parser.parse_args()

    migration = Migration(load_graph())
    documents = migration.build()
    for warning in migration.warnings:
        print(f"warning: {warning}")
    for collection in CLASSES:
        print(f"built {collection}: {len(documents[collection])}")
    if args.dry_run:
        return

    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[DB_NAME]
    populated = [name for name in COLLECTIONS if name in db.list_collection_names() and db[name].estimated_document_count()]
    if populated and not args.drop:
        sys.exit(f"Collections already contain data: {', '.join(populated)}. Use --drop to replace them.")
    for name in COLLECTIONS:
        db.drop_collection(name)
    ensure_schema(db)
    for collection in CLASSES:
        db[collection].insert_many(documents[collection], ordered=True)
        print(f"{collection}: {db[collection].count_documents({})}")
    client.close()


if __name__ == "__main__":
    main()
