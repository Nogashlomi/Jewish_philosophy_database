---
name: db-snapshot
description: Dump the jephy MongoDB database (all collections, read-only) to data/db_snapshot.json for offline lookups, dedup against existing records, and data-import preparation. Use before any extraction or import work that needs to know what is already in the DB, and after every import.
---

# jephy DB snapshot

Read-only dump of every collection in `COLLECTIONS` (`backend/app/core/db_schema.py`) to `data/db_snapshot.json`, keyed by collection name, plus `taken_at`. Nothing is written to the DB.

Run from the repo root:

```bash
MONGODB_URI="$(grep -E '^MONGODB_URI=' backend/.env | cut -d= -f2-)" uv run --project data_pipeline python .claude/skills/db-snapshot/scripts/snapshot_db.py
```

`--out <path>` writes elsewhere.

Take a fresh snapshot before work that dedups against the DB, and again after every import, so later runs see the imported records. Check `taken_at` to judge whether an existing snapshot is stale.
