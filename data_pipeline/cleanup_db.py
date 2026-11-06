import argparse
import copy
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from pymongo import DeleteOne, InsertOne, MongoClient, ReplaceOne

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.db_schema import COLLECTIONS, ensure_schema, new_id

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = REPO / "data" / "sep_import" / "db_cleanup_plan.json"
BACKUP_DIR = REPO / "data" / "db_backups"
DB_NAME = "jephy"
QUALIFIER = re.compile(r"\s*\(.*$")


def unique(values) -> list:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def base_name(name: str) -> str:
    return QUALIFIER.sub("", name).rstrip("?. ").strip()


def qualifier(name: str) -> str:
    match = re.search(r"\((.*)$", name)
    return match.group(1).rstrip(")").strip() if match else ""


def bson_ok(value, t: str) -> bool:
    return {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "double": lambda v: isinstance(v, float),
        "bool": lambda v: isinstance(v, bool),
    }[t](value)


def validate(value, schema: dict, path: str = "") -> list:
    if "bsonType" in schema and not bson_ok(value, schema["bsonType"]):
        return [f"{path or '/'}: expected {schema['bsonType']}"]
    errors = []
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not allowed")
    if "pattern" in schema and not re.search(schema["pattern"], value):
        errors.append(f"{path}: {value!r} bad pattern")
    if isinstance(value, dict):
        errors += [f"{path}.{k}: required" for k in schema.get("required", []) if k not in value]
        for k, v in value.items():
            if k in schema.get("properties", {}):
                errors += validate(v, schema["properties"][k], f"{path}.{k}")
    if isinstance(value, list):
        for i, v in enumerate(value):
            errors += validate(v, schema.get("items", {}), f"{path}[{i}]")
    return errors


class Cleanup:
    def __init__(self, data: dict):
        self.docs = {c: {d["_id"]: d for d in data[c]} for c in COLLECTIONS}
        self.original = copy.deepcopy(self.docs)
        self.deleted = {c: set() for c in COLLECTIONS}
        self.created = {c: set() for c in COLLECTIONS}
        self.log = []

    def repoint(self, old: str, new: str):
        for person in self.docs["persons"].values():
            for item in person["places"]:
                if item["place"] == old:
                    item["place"] = new
            for relation in person["relations"]:
                if relation["target"] == old:
                    relation["target"] = new
            person["relations"] = unique(person["relations"])
        for work in self.docs["works"].values():
            for field in ("authors", "translators"):
                work[field] = unique(new if x == old else x for x in work[field])
            for field in ("translation_of", "commentary_on"):
                if work.get(field) == old:
                    work[field] = new

    def merge_common(self, keep: dict, other: dict, alt_field: str | None):
        for field in ("sources", "subjects", "languages", "notes", "times", "places", "relations", "authors", "translators"):
            if field in other:
                keep[field] = unique(keep.get(field, []) + other[field])
        for field in ("description", "viaf_id", "location", "authorship_status", "preservation_status", "translation_of", "commentary_on"):
            if field in other and field not in keep:
                keep[field] = other[field]
        if alt_field:
            label = "title" if alt_field == "alt_titles" else "name"
            names = [base_name(other[label])] + other.get(alt_field, [])
            keep[alt_field] = unique(n for n in keep.get(alt_field, []) + names if n and n != keep[label])
        if "times" in keep:
            keep["times"].sort(key=lambda t: t["from"])

    def merge(self, op: dict):
        collection, keep_id = op["collection"], op["keep"]
        keep = self.docs[collection][keep_id]
        alt_field = {"persons": "alt_names", "works": "alt_titles"}.get(collection)
        for other_id in op["remove"]:
            other = self.docs[collection].get(other_id)
            if other is None:
                self.log.append(f"skip merge: {other_id} missing")
                continue
            self.merge_common(keep, other, alt_field)
            if collection == "persons":
                note = qualifier(other["name"]) or ("?" if other["name"].rstrip().endswith("?") else "")
                if note:
                    for work in self.docs["works"].values():
                        if other_id in work["authors"] + work["translators"]:
                            work["notes"] = unique(work.get("notes", []) + [f"Recorded attribution: {other['name']}"])
                            if "?" in other["name"] and other_id in work["authors"] and "authorship_status" not in work:
                                work["authorship_status"] = "questioned"
            if collection == "places":
                tag = op.get("qualifiers_to_description", {}).get(other_id)
                if tag:
                    for person in self.docs["persons"].values():
                        for item in person["places"]:
                            if item["place"] == other_id:
                                item["description"] = f"{item['description']} ({tag})" if item.get("description") else tag
            self.repoint(other_id, keep_id)
            del self.docs[collection][other_id]
            self.deleted[collection].add(other_id)
            self.log.append(f"merged {collection} {other_id} ({other.get('name') or other.get('title')}) -> {keep_id}")
        if collection == "persons":
            for person in self.docs["persons"].values():
                person["relations"] = [r for r in person["relations"] if r["target"] != person["_id"]]
        for field, value in op.get("set", {}).items():
            keep[field] = value

    def split_work(self, op: dict):
        work = self.docs["works"][op["work"]]
        original_sources = work["sources"]
        for part in op.get("new", []):
            new_doc = {k: copy.deepcopy(v) for k, v in work.items() if k in ("title", "languages")}
            new_doc["subjects"] = part.get("subjects", [])
            new_id_value = new_id("work")
            while new_id_value in self.docs["works"]:
                new_id_value = new_id("work")
            matched = [s for s in original_sources if any(m in s.get("url", "") for m in part.get("source_urls_containing", []))]
            new_doc.update({"_id": new_id_value, "authors": part["authors"], "translators": [], "sources": part["sources"] if "sources" in part else matched})
            if part.get("description"):
                new_doc["description"] = part["description"]
            self.docs["works"][new_id_value] = new_doc
            self.created["works"].add(new_id_value)
            self.log.append(f"split {op['work']} ({work['title']}): new {new_id_value} for {part['authors']}")
        moved = {a for part in op.get("new", []) for a in part["authors"]} | set(op.get("remove_authors", []))
        work["authors"] = [a for a in work["authors"] if a not in moved]
        drop_urls = [m for part in op.get("new", []) for m in part.get("source_urls_containing", [])]
        work["sources"] = [s for s in work["sources"] if not any(m in s.get("url", "") for m in drop_urls)] or work["sources"]
        for field, value in op.get("set", {}).items():
            work[field] = value

    def set_fields(self, op: dict):
        doc = self.docs[op["collection"]][op["_id"]]
        for field, value in op["set"].items():
            doc[field] = value
        for field, values in op.get("add", {}).items():
            doc[field] = unique(doc.get(field, []) + values)
        self.log.append(f"set {op['collection']} {op['_id']}: {list(op['set']) + list(op.get('add', {}))}")

    def remove_elements(self, op: dict):
        doc = self.docs[op["collection"]][op["_id"]]
        before = len(doc[op["field"]])
        doc[op["field"]] = [e for e in doc[op["field"]] if not all(e.get(k) == v for k, v in op["match"].items())]
        self.log.append(f"removed {before - len(doc[op['field']])} {op['field']} from {op['_id']}")

    def fix_parentheses(self):
        for collection in ("places", "persons"):
            for doc in self.docs[collection].values():
                name = doc["name"]
                if name.count("(") > name.count(")"):
                    doc["name"] = name.rstrip() + ")"
                    self.log.append(f"closed parenthesis: {collection} {doc['_id']} {doc['name']}")

    def apply(self, plan: dict):
        for op in plan.get("split_work", []):
            self.split_work(op)
        for op in plan.get("merge", []):
            self.merge(op)
        for op in plan.get("set", []):
            self.set_fields(op)
        for op in plan.get("remove_elements", []):
            self.remove_elements(op)
        if plan.get("fix_unbalanced_parentheses"):
            self.fix_parentheses()

    def check(self) -> list:
        errors = []
        ids = {i for c in COLLECTIONS for i in self.docs[c]}
        for collection in COLLECTIONS:
            for doc in self.docs[collection].values():
                errors += [f"{collection} {doc['_id']}{e}" for e in validate(doc, COLLECTIONS[collection])]
                for ref in re.findall(r'"((?:person|work|place|subject|language|source)_[a-z0-9]{8})"', json.dumps({k: v for k, v in doc.items() if k != "_id"})):
                    if ref not in ids:
                        errors.append(f"{collection} {doc['_id']}: dangling {ref}")
        return errors

    def operations(self) -> dict:
        ops = {}
        for collection in COLLECTIONS:
            batch = [DeleteOne({"_id": i}) for i in sorted(self.deleted[collection])]
            for doc_id, doc in self.docs[collection].items():
                if doc_id in self.created[collection]:
                    batch.append(InsertOne(doc))
                elif doc != self.original[collection].get(doc_id):
                    batch.append(ReplaceOne({"_id": doc_id}, doc))
            if batch:
                ops[collection] = batch
        return ops


def main():
    parser = argparse.ArgumentParser(description="Apply a reviewed DB cleanup plan (merges, work splits, field fixes) to the jephy database.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--dry-run", action="store_true", help="Compute and validate changes without writing")
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[DB_NAME]
    data = {c: list(db[c].find({})) for c in COLLECTIONS}

    cleanup = Cleanup(data)
    cleanup.apply(plan)
    for line in cleanup.log:
        print(line)
    errors = cleanup.check()
    for error in errors:
        print(f"error: {error}")
    ops = cleanup.operations()
    for collection, batch in ops.items():
        kinds = {}
        for op in batch:
            kinds[type(op).__name__] = kinds.get(type(op).__name__, 0) + 1
        print(f"{collection}: {kinds}")
    if errors:
        sys.exit("validation failed; nothing written")
    if args.dry_run:
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"pre-cleanup-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    backup.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"backup written {backup}")
    ensure_schema(db)
    for collection, batch in ops.items():
        result = db[collection].bulk_write(batch, ordered=True)
        print(f"{collection}: inserted {result.inserted_count}, modified {result.modified_count}, deleted {result.deleted_count}")
    client.close()


if __name__ == "__main__":
    main()
