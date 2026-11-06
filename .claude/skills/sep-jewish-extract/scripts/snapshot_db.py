import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "backend"))

from app.core.db_schema import COLLECTIONS

DB_NAME = "jephy"
DEFAULT_OUT = REPO / "data" / "sep_import" / "db_snapshot.json"


def main():
    parser = argparse.ArgumentParser(description="Dump the jephy MongoDB collections (read-only) for SEP dedup and merging.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[DB_NAME]
    snapshot = {"taken_at": datetime.now(timezone.utc).isoformat()}
    for name in COLLECTIONS:
        snapshot[name] = list(db[name].find({}))
        print(f"{name}: {len(snapshot[name])}")
    client.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"written {args.out}")


if __name__ == "__main__":
    main()
