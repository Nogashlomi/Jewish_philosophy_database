---
name: sep-jewish-extract
description: Extract Jewish persons and their derived data (works, places, times, subjects, languages, relations) from the local Stanford Encyclopedia of Philosophy export into MongoDB-ready JSON for the jephy database, deduplicated against the existing DB and with per-datum SEP provenance. Use when asked to mine, extract or import SEP entries.
---

# SEP → jephy extraction

Reads the SEP export at `/home/liri/Stanford_Encyclopedia_of_Philosophy__Dump/export` (`json/<id>.json` for metadata and TOC, `md/<id>.md` for reading) and produces import-ready JSON. This skill **does not write to MongoDB**; importing is a separate step.

All working files live in `data/sep_import/` (repo root):

| Path | Written by | Content |
|---|---|---|
| `db_snapshot.json` | `snapshot_db.py` (user runs it) | Read-only dump of every collection, used for dedup |
| `candidates.json` | `candidates.py` | Ranked SEP entries likely to involve Jewish persons |
| `entries/<id>.json` | you / subagents | Per-entry extraction (format: `references/extraction_format.md`) |
| `ids.json` | `assemble.py` | Stable mapping of extracted entities to generated IDs; keep it between runs |
| `out/<collection>.json` | `assemble.py` | New documents, schema-valid, one array per collection |
| `out/updates.json` | `assemble.py` | Additions to existing DB records |
| `out/report.json` | `assemble.py` | Unresolved matches, review items, dropped refs, validation errors |

Scripts are in `.claude/skills/sep-jewish-extract/scripts/`. Paths below are relative to the repo root.

## 1. DB snapshot (user)

Dedup needs the current DB. If `data/sep_import/db_snapshot.json` is missing or older than the last DB change, ask the user to run:

```bash
cd data_pipeline && MONGODB_URI="$(grep -E '^MONGODB_URI=' ../backend/.env | cut -d= -f2-)" uv run python ../.claude/skills/sep-jewish-extract/scripts/snapshot_db.py
```

Do not run it yourself. Re-snapshot after every import so the next run sees the imported records.

## 2. Candidates

```bash
python3 .claude/skills/sep-jewish-extract/scripts/candidates.py
```

Tiers in `candidates.json`:

- `biography`: entry about a person, with Jewish keyword density or ancestry sentences (`ancestry_evidence`). Includes false positives (e.g. Christian Hebraists); your extraction decides.
- `topical`: thematic entries dense with Jewish content (e.g. `arabic-islamic-judaic`, `medieval-philosophy`); mine them for Jewish persons discussed with concrete data.
- `mentions`: everything else with any hit. Only grep the Jewish passages in these (`grep -n -i -E "jew|judaism|hebrew|rabbi|talmud|kabbal" md/<id>.md`) for persons not covered elsewhere; skip the tier if the user asked for a quick pass.

Also check your own knowledge for SEP biography entries on persons of Jewish birth whose entry may not say so (e.g. Wittgenstein, Popper): process them; the extraction marks them `"jewish": "uncertain"` unless the text gives evidence.

Present the counts and the list of `biography` + `topical` entries to the user before extracting, and confirm the scope.

## 3. Extract per entry

Skip entries that already have `data/sep_import/entries/<id>.json` unless the user asks to redo them.

For each entry: read `md/<id>.md` in full, take section titles from `json/<id>.json` → `toc`, look up every entity with `lookup.py`, and write the entry file exactly per `references/extraction_format.md`.

Process `biography` entries first (they create the canonical persons), then `topical`, then `mentions`, so later entries can link to earlier ones via `lookup.py` (`[sep]` results).

Parallelize with subagents, about 4 entries each, at most 5 at a time; wait for a wave to finish before starting the next so lookups see earlier results. Prompt for each subagent:

> Extract Jewish persons and their works, places, times and relations from these Stanford Encyclopedia of Philosophy entries: `<id1>, <id2>, ...`. Repo root: `/home/liri/Jewish_philosophy_database`. First read `.claude/skills/sep-jewish-extract/references/extraction_format.md` and follow it exactly. Source files: `/home/liri/Stanford_Encyclopedia_of_Philosophy__Dump/export/md/<id>.md` (read the whole file) and `.../json/<id>.json` (use its `toc` for section names). Use `lookup.py` for every person, work and place before writing it. Write one file per entry to `data/sep_import/entries/<id>.json`. Do not edit any other file. Report per entry: persons extracted (Jewish / stub / uncertain), works count, and anything you were unsure about.

After each wave, spot-check one or two files against the source text (evidence quotes, years, sections).

## 4. Assemble

```bash
uv run --project data_pipeline python .claude/skills/sep-jewish-extract/scripts/assemble.py
```

(`uv` is needed only because `db_schema.py` imports pymongo; nothing touches the DB.)

What it does:

- Groups the same entity across entries (`db_id`, `same_as`, shared name variant + compatible dates for persons, shared author for works).
- Matches groups to the snapshot: explicit `db_id`, else a unique exact name match (dates and authors must agree). Several matches, or a near-duplicate name, makes the group `unresolved`: nothing is emitted for it until you decide.
- Emits Jewish persons with their works and places, and non-Jewish persons only as stubs that a Jewish person's relation or work needs. Existing non-Jewish persons are referenced but never changed.
- Provenance: every person/work/place/subject gets `sources: [{source: <SEP source id>, url: <entry URL>}]`, one per entry it came from; every `times`, `places` and `relations` item gets `source` + `source_url` pointing at the entry section. The SEP source record is reused from the DB (`Stanford Encyclopedia of Philosophy`) or created in `out/sources.json`.
- Existing records are never overwritten: `updates.json` only adds new alt names, sources, subjects, languages, times, places, relations, authors, and fills fields that are missing. Conflicting values are listed under `kept_existing_values`.
- Validates new documents, and existing documents with the updates applied, against `COLLECTIONS` in `backend/app/core/db_schema.py`.

## 5. Resolve the report

Work through `out/report.json` and re-run `assemble.py` until it is clean:

- `unresolved`: decide using the candidates listed, then set `db_id`, `same_as` or `confirmed_new: true` in the entry file(s).
- `review_uncertain_jewish`: ask the user; on approval, set `"jewish": true` and put the user's decision in `jewish_evidence.reason` (keep the quote empty only if the user accepts that).
- `dropped_refs`, `unknown_sections`, `dropped_data`, `validation_errors`, `errors`: fix the entry files.
- `merged_*`: check that nothing unrelated was merged; if it was, give the items distinct names or set `confirmed_new`/`db_id`.
- `new_subjects`, `new_languages`: rename to an existing name where one fits.
- `kept_existing_values`: show the user; they decide whether the DB value should change.

## 6. Hand over

Summarize counts (new per collection, updates, open review items) and point the user to `data/sep_import/out/`. The import step (not part of this skill) must:

1. Apply the current `db_schema.py` (start the backend or call `ensure_schema`) first: this skill relies on the `student_of` relation type, relation `source`/`source_url`, and work `alt_titles`/`times`/`commentary_on`.
2. Insert `out/*.json` in order: sources, languages, subjects, places, persons, works. Load them with Python `json` + pymongo so years stay `int` and coordinates stay `double`.
3. For each item in `updates.json`: `$addToSet: {field: {$each: values}}` for `add_to_set`, and `$set` for each `set_if_missing` field guarded by `{field: {$exists: false}}`.
4. Re-run the snapshot.
