import argparse
import json
import os
import sys
from pathlib import Path

from pymongo import InsertOne, MongoClient, UpdateOne

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.db_schema import ensure_schema

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sep_import" / "out"
DB_NAME = "jephy"
INSERT_ORDER = ("sources", "languages", "subjects", "places", "persons", "works")


def load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def main():
    parser = argparse.ArgumentParser(description="Import the SEP extraction output (new documents and updates) into MongoDB.")
    parser.add_argument("--dir", type=Path, default=OUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing to MongoDB")
    args = parser.parse_args()

    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[DB_NAME]
    if not args.dry_run:
        ensure_schema(db)

    for collection in INSERT_ORDER:
        docs = load(args.dir / f"{collection}.json")
        if not docs:
            continue
        existing = {d["_id"] for d in db[collection].find({"_id": {"$in": [d["_id"] for d in docs]}}, {"_id": 1})}
        for doc_id in sorted(existing):
            print(f"warning: {collection} {doc_id} already exists, skipped")
        operations = [InsertOne(d) for d in docs if d["_id"] not in existing]
        print(f"{collection}: {len(operations)} to insert")
        if operations and not args.dry_run:
            result = db[collection].bulk_write(operations, ordered=True)
            print(f"{collection}: inserted {result.inserted_count}")

    updates = load(args.dir / "updates.json")
    operations = {}
    for update in updates:
        collection, doc_id = update["collection"], update["_id"]
        if not db[collection].count_documents({"_id": doc_id}, limit=1):
            print(f"warning: {collection} {doc_id} ({update.get('label')}) not found, update skipped")
            continue
        ops = operations.setdefault(collection, [])
        add = update.get("add_to_set", {})
        if add:
            ops.append(UpdateOne({"_id": doc_id}, {"$addToSet": {field: {"$each": values} for field, values in add.items()}}))
        for field, value in update.get("set_if_missing", {}).items():
            ops.append(UpdateOne({"_id": doc_id, field: {"$exists": False}}, {"$set": {field: value}}))
        for change in update.get("set_element_fields", []):
            element_filter = {f"e.{k}": v if v is not None else {"$exists": False} for k, v in change["match"].items()}
            element_filter["e.source"] = {"$exists": False}
            ops.append(UpdateOne(
                {"_id": doc_id},
                {"$set": {f"{change['field']}.$[e].{k}": v for k, v in change["set"].items()}},
                array_filters=[element_filter],
            ))
    for collection, ops in operations.items():
        print(f"{collection}: {len(ops)} update operations")
        if ops and not args.dry_run:
            result = db[collection].bulk_write(ops, ordered=True)
            print(f"{collection}: modified {result.modified_count}")
    client.close()


if __name__ == "__main__":
    main()
