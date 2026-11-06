---
name: sep-jewish-extract
description: Extract Jewish persons and their derived data (works, places, times, subjects, languages, relations) from the local Stanford Encyclopedia of Philosophy export into MongoDB-ready JSON for the jephy database, deduplicated against the existing DB and with per-datum SEP provenance. Use when asked to mine, extract or import SEP entries.
---

# SEP → jephy extraction

Reads the SEP export at `/home/liri/Stanford_Encyclopedia_of_Philosophy__Dump/export` (`json/<id>.json` for metadata and TOC, `md/<id>.md` for reading) and produces import-ready JSON. This skill **does not write to MongoDB**; importing is a separate step.

Working files live in `data/sep_import/` (repo root) and are temporary: delete the directory once the run is imported and its open cases are handed over (step 7). Two files persist: the DB snapshot `data/db_snapshot.json` (gitignored, refreshed by the `db-snapshot` skill) and `data/sep_ids.json` (committed).

| Path | Written by | Content |
|---|---|---|
| `candidates.json` | `candidates.py` | Ranked SEP entries likely to involve Jewish persons |
| `entries/<id>.json` | you / subagents | Per-entry extraction (format: `references/extraction_format.md`) |
| `data/sep_ids.json` (permanent) | `assemble.py` | Maps each extracted entity (`<entry>/<key>`) to the DB id it was given; makes re-runs recognise records an earlier run created. Never delete it; commit it after each import |
| `out/<collection>.json` | `assemble.py` | New documents, schema-valid, one array per collection |
| `out/updates.json` | `assemble.py` | Additions to existing DB records |
| `out/report.json` | `assemble.py` | Unresolved matches, review items, dropped refs, validation errors, `db_cleanup` |
| `verification/*.json` | subagents | External-source checks of Jewish identity (step 5) |
| `db_cleanup_notes.json` | you / subagents | Hand-noted DB issues found during extraction |
| `db_cleanup_plan.json` | you | Reviewed cleanup plan for `data_pipeline/cleanup_db.py` (step 6) |

Scripts are in `.claude/skills/sep-jewish-extract/scripts/`. Paths below are relative to the repo root.

## 1. DB snapshot

Dedup needs the current DB. If `data/db_snapshot.json` is missing or older than the last DB change, run the `db-snapshot` skill.

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
- Emits Jewish persons with their works and places, and non-Jewish persons only as stubs that a Jewish person's relation or work needs. Persons marked `uncertain` who already exist in the DB are upserted fully (the DB already holds them); new uncertain persons wait for review.
- Provenance: every person/work/place/subject gets `sources: [{source: <SEP source id>, url: <entry URL>}]`, one per entry it came from; every `times`, `places` and `relations` item gets `source` + `source_url` pointing at the entry section. The SEP source record is reused from the DB (`Stanford Encyclopedia of Philosophy`) or created in `out/sources.json`.
- Upserts existing records without overwriting anything, so no SEP finding is lost because a record already exists:
  - `add_to_set`: new alt names, sources, subjects, languages, authors, translators, notes, and `times`/`places`/`relations` items not yet present.
  - `set_element_fields`: when the DB already has the same time/place/relation item but without a source, the SEP `source`/`source_url` (and a missing description) are attached to it in place.
  - A matching item that already carries another source gets the SEP item added alongside it (corroborating provenance); a conflicting lifespan/birth/death is added with its SEP source and listed under `conflicting_values_added`.
  - `set_if_missing`: description, statuses, `translation_of`, `commentary_on`, location. A differing SEP description is added to `notes` as `SEP (<url>): …`; other differing scalar values are listed under `kept_existing_values`.
- Validates new documents, and existing documents with the updates applied, against `COLLECTIONS` in `backend/app/core/db_schema.py`.

## 5. Resolve the report

Work through `out/report.json` and re-run `assemble.py` until it is clean:

- `unresolved`: decide using the candidates listed, then set `db_id`, `same_as` or `confirmed_new: true` in the entry file(s).
- `review_uncertain_jewish`: never decide from common knowledge. Verify each person against an explicit online source (subagents with WebSearch/WebFetch; prefer Britannica, Jewish Encyclopedia, YIVO, Encyclopaedia Judaica/JVL, Deutsche Biographie, MacTutor, IEP, university/archive biographies; Wikipedia only when nothing better states it). Record results in `data/sep_import/verification/*.json` (`name`, `refs`, `verdict` jewish/not_jewish/unverified, `source_name`, `url`, verbatim `quote`, `notes`). For `jewish`, set the person's `"jewish": true` and `jewish_evidence.external = {source_name, url, quote}` in each referenced entry file; `assemble.py` adds that source to the person's `sources` (reusing an existing source record by name, e.g. Wikipedia, JE, or creating one) and a "Jewish identity (<source>, <url>)" note. Leave `unverified`/`not_jewish` as they are.
- `uncertain_in_db_assumed_jewish`: informational; uncertain persons already in the DB are treated as Jewish and upserted.
- `dropped_refs`, `unknown_sections`, `dropped_data`, `validation_errors`, `errors`: fix the entry files.
- `merged_*`: check that nothing unrelated was merged; if it was, give the items distinct names or set `confirmed_new`/`db_id`.
- `new_subjects`, `new_languages`: rename to an existing name where one fits.
- `kept_existing_values`, `conflicting_values_added`: show the user; they decide whether the DB value should change.
- `db_cleanup`: issues in the existing DB to fix later, not by this skill:
  - `duplicate_records`: same-name groups detected from the snapshot (persons need compatible dates; works need a shared author/translator/original). `kind` is `duplicate` or `numbered_variants_maybe_intentional` for "(1)/(2)…" series. `touched_by_sep_import` lists which of the records this import updates or references.
  - `suspected_merged_works`: one work record whose authors lived over a century apart.
  - `suspect_coordinates`: same-name places more than 100 km apart.
  - `conflicting_dates`: lifespan/birth/death values the import added next to a differing DB value.
  - `noted_during_extraction`: issues recorded by hand in `data/sep_import/db_cleanup_notes.json` (merged works, wrong coordinates, misspelt names, SEP typos, possible identities). Append to that file whenever extraction surfaces such an issue.
  - To act on them: write a reviewed plan (`merge` with `keep`/`remove`/optional `set` and `qualifiers_to_description`, `split_work` with `remove_authors`/`new`, `set` with optional `add`, `remove_elements`, `fix_unbalanced_parentheses`) and run `data_pipeline/cleanup_db.py --dry-run`, then without it. It repoints every reference before deleting a merged record, turns qualifiers of merged person names ("?", "the author himself") into work notes, validates against the schema, and writes a full backup to `data/db_backups/` first. After a cleanup, repoint `db_id`s in `data/sep_import/entries/` from removed to kept records, and re-run the `db-snapshot` skill.

## 6. Import, verify, clean up the DB

Summarize counts (new per collection, updates, open review items) and get the user's go-ahead before writing to the DB. The import must:

1. Apply the current `db_schema.py` (start the backend or call `ensure_schema`) first: this skill relies on the `student_of` relation type, relation `source`/`source_url`, and work `alt_titles`/`times`/`commentary_on`.
2. Insert `out/*.json` in order: sources, languages, subjects, places, persons, works. Load them with Python `json` + pymongo so years stay `int` and coordinates stay `double`.
3. For each item in `updates.json`: `$addToSet: {field: {$each: values}}` for `add_to_set`; `$set` for each `set_if_missing` field guarded by `{field: {$exists: false}}`; for `set_element_fields`, `$set` on `<field>.$[e].<key>` with an array filter matching `match` and `e.source` missing. `data_pipeline/import_sep.py` does all of this.
4. Re-run the `db-snapshot` skill, check every new record and update value is present and no reference dangles, and sanity-check the deployed API with a small sample of list and detail requests.
5. Commit `data/sep_ids.json`.

Then act on `db_cleanup` (see step 5): put the cases that are clear-cut into `data/sep_import/db_cleanup_plan.json`, dry-run and run `data_pipeline/cleanup_db.py --plan data/sep_import/db_cleanup_plan.json`, re-snapshot, and repoint any `db_id`s in the entry files that pointed to merged-away records (so a re-assembly stays idempotent: it must yield no new records).

## 7. Hand over and clean up

Write the cases that need a human decision (unverified or weakly sourced Jewish identities, possible identities, work duplicates and multi-author records, numbered "(n)" series, conflicting dates, kept-DB-vs-SEP values, new subjects) to a Markdown file in the repo root for the team, e.g. `db_open_cases.md`, with record ids and the decision needed for each. Then delete `data/sep_import/`; keep `data/sep_ids.json`.
