import argparse
import csv
import os
import re
import sys
from pathlib import Path

from pymongo import MongoClient, UpdateOne

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.db_schema import ensure_schema

VIAF_CSV = Path(__file__).resolve().parent.parent / "data" / "viaf_lookup.csv"
DB_NAME = "jephy"
MAX_RESULTS = 3
TRAILING_DATES = re.compile(r",\s*[^,]*\d[^,]*$")


def normalize_name(viaf_name: str) -> str:
    return TRAILING_DATES.sub("", viaf_name).strip()


def load_suggestions() -> dict:
    suggestions = {}
    with open(VIAF_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for i in range(1, MAX_RESULTS + 1):
                viaf_id = (row.get(f"viaf_id_{i}") or "").strip()
                viaf_name = (row.get(f"viaf_name_{i}") or "").strip()
                if viaf_id and viaf_name:
                    suggestions.setdefault(row["name"].strip(), []).append(
                        {"viaf_id": viaf_id, "viaf_name": viaf_name, "name": normalize_name(viaf_name)}
                    )
    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Attach VIAF name suggestions from viaf_lookup.csv to persons.")
    parser.add_argument("--dry-run", action="store_true", help="Report matches without writing to MongoDB")
    args = parser.parse_args()

    suggestions = load_suggestions()
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[DB_NAME]

    updates = []
    matched_names = set()
    for person in db.persons.find({"name_verified": {"$ne": True}}, {"name": 1, "alt_names": 1}):
        person_suggestions = {}
        for name in [person["name"]] + person["alt_names"]:
            for suggestion in suggestions.get(name, []):
                person_suggestions.setdefault(suggestion["viaf_id"], suggestion)
                matched_names.add(name)
        if person_suggestions:
            updates.append(UpdateOne({"_id": person["_id"]}, {"$set": {"viaf_suggestions": list(person_suggestions.values())}}))

    for name in sorted(set(suggestions) - matched_names):
        print(f"warning: no unverified person named {name!r}")
    print(f"persons with suggestions: {len(updates)}")
    if args.dry_run:
        return

    ensure_schema(db)
    if updates:
        result = db.persons.bulk_write(updates)
        print(f"updated: {result.modified_count}")
    client.close()


if __name__ == "__main__":
    main()
