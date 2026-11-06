# Per-entry extraction format

One file per SEP entry: `data/sep_import/entries/<identifier>.json`. It describes what the entry says, using local keys. `assemble.py` turns it into database IDs, merges it with other entries and the DB, and adds provenance URLs. Do not write database documents by hand.

## Ground rules

- **SEP is the only source of facts.** Every person, date, place, work and relation must be stated in the entry (main text, preamble, notes, bibliography or supplements). Your own knowledge may be used only to (a) give coordinates for a place, (b) recognise that a name refers to an existing DB record, (c) mark someone `"jewish": "uncertain"`.
- **Every datum carries a `section`**: the exact TOC title from the entry's JSON `toc` (e.g. `"2. Biography"`, `"4.2 Sources"`), or one of `"preamble"`, `"notes"`, `"bibliography"`, or a supplement file name. `assemble.py` turns it into `source_url` (`https://plato.stanford.edu/entries/<id>/#<anchor>`). A wrong section is reported as `unknown_sections`.
- Add `quote` (a short verbatim fragment, ≤ 200 chars) wherever it helps a reviewer; it is not imported.
- Never invent precision: `c. 1160` → `"from": 1160, "estimated": true`. "12th century" → `"from": 1100, "until": 1199, "estimated": true`. BCE years are negative integers.

## Which persons to extract

| Person | Extract |
|---|---|
| Subject of a biographical entry, Jewish | Everything: `"entry_subject": true` |
| Other Jewish person with at least one concrete datum (dates, place, work, teacher/student, relation) | Everything the entry says about them |
| Jewish person only name-dropped | Skip; list in `skipped` |
| Non-Jewish person who is a relation target of a Jewish person, or authored a work a Jewish person translated or commented on | Minimal stub: `name`, `alt_names`, lifespan `times`, `"jewish": false` |
| Anyone else | Skip |

**Jewish** means: born Jewish (including later converts such as conversos, Abner of Burgos, Husserl), converted to Judaism, Karaites, Samaritans. Set `"jewish": true` with a `jewish_evidence.quote` from the SEP text that shows it, either explicitly ("born into a Jewish family") or through context that leaves no real doubt: the person is a rabbi, writes Hebrew Bible or Talmud commentary, takes part in a Jewish controversy or community, translates for a Jewish readership, or is presented among "Jewish philosophers" (e.g. David Kimhi, Solomon ibn Adret, Judah Ibn Tibbon are `true`). Add `jewish_evidence.reason` when the quote is contextual. Use `"jewish": "uncertain"` only when the entry gives no such evidence (e.g. a modern philosopher whose entry never mentions their background) or the evidence is ambiguous (e.g. a possible convert); explain in `reason`. Uncertain persons that already exist in the DB are treated as Jewish (the DB already holds them); new uncertain persons are not imported until their Jewish identity is verified against an explicit external source (see `SKILL.md`, step 5), recorded as `jewish_evidence.external: {"source_name": "...", "url": "...", "quote": "..."}`.

## Deduplication (required for every person, work and place)

Before writing an entity, look it up:

```bash
python3 .claude/skills/sep-jewish-extract/scripts/lookup.py persons "Abraham ibn Daud"
python3 .claude/skills/sep-jewish-extract/scripts/lookup.py works "Emunah Ramah"
python3 .claude/skills/sep-jewish-extract/scripts/lookup.py places "Toledo"
python3 .claude/skills/sep-jewish-extract/scripts/lookup.py subjects --list
python3 .claude/skills/sep-jewish-extract/scripts/lookup.py languages --list
```

Results tagged `[db]` are existing records; `[sep]` are entities already extracted from other entries.

- Same entity in the DB → set `"db_id"` to its id (check dates/authors, not only the name). New SEP data is added to that record; nothing in it is overwritten.
- Same entity already extracted from another entry → add `"same_as": ["sep:<entry>/<key>"]`.
- Similar name but a different entity (e.g. Moses ibn Ezra vs. Abraham ibn Ezra) → set `"confirmed_new": true`.
- Not found → nothing; `assemble.py` creates it. If it finds a near-duplicate you did not resolve, it refuses to emit the entity and lists it under `unresolved`.

Subjects and languages are matched by exact name: reuse the names printed by `--list`. Only introduce a new subject when none fits.

## References

Wherever a field points to another entity (`place`, `authors`, `translators`, `target`, `translation_of`, `commentary_on`), use one of:

- a local `key` from this file (preferred; add a stub entity if needed);
- `"sep:<entry>/<key>"` for an entity in another entry file;
- an existing DB id (`person_ab12cd34`);
- `"name:<Name>"` as a last resort (dropped unless exactly one record matches).

## Schema

```json
{
  "entry": "abraham-daud",
  "status": "extracted",
  "persons": [
    {
      "key": "ibn-daud",
      "entry_subject": true,
      "db_id": null,
      "same_as": [],
      "confirmed_new": false,
      "jewish": true,
      "jewish_evidence": {"section": "preamble", "quote": "a pioneer in Jewish philosophy"},
      "name": "Abraham Ibn Daud",
      "alt_names": ["Abraham ben David Halevi", "Rabad I"],
      "description": "Twelfth-century Andalusian philosopher, astronomer and historian; author of the first systematic Aristotelian treatise in Jewish thought.",
      "notes": [],
      "subjects": ["Philosophy", "Aristotelianism"],
      "languages": ["Judeo-Arabic", "Hebrew"],
      "times": [
        {"type": "lifespan", "from": 1110, "until": 1180, "estimated": true, "description": "c.1110–1180", "section": "preamble"}
      ],
      "places": [
        {"place": "cordoba", "type": "birth", "from": 1110, "estimated": true, "section": "2. Biography", "quote": "born in Córdoba"},
        {"place": "toledo", "type": "residence", "description": "Settled in Toledo after the Almohad invasion.", "section": "2. Biography"}
      ],
      "relations": [
        {"type": "influenced_by", "target": "ibn-sina", "target_kind": "persons", "description": "Draws heavily on Avicenna's psychology.", "section": "4.2 Sources"}
      ]
    },
    {
      "key": "ibn-sina",
      "db_id": "person_x1y2z3w4",
      "jewish": false,
      "name": "Ibn Sina",
      "alt_names": ["Avicenna"],
      "times": [{"type": "lifespan", "from": 980, "until": 1037, "section": "4.2 Sources"}]
    }
  ],
  "works": [
    {
      "key": "emunah-ramah",
      "db_id": null,
      "title": "ha-Emunah ha-Ramah",
      "alt_titles": ["The Exalted Faith", "al-ʿAqīda al-rafīʿa"],
      "authors": ["ibn-daud"],
      "translators": [],
      "translation_of": null,
      "commentary_on": null,
      "languages": ["Judeo-Arabic"],
      "subjects": ["Philosophy"],
      "description": "Philosophical treatise integrating Aristotelianism into Jewish thought, written to solve the problem of free will.",
      "authorship_status": "authored",
      "times": [{"type": "composition", "from": 1160, "estimated": true, "section": "3. Major Works"}],
      "section": "3. Major Works"
    }
  ],
  "places": [
    {"key": "cordoba", "db_id": "place_q9w8e7r6", "name": "Córdoba"},
    {"key": "toledo", "db_id": null, "name": "Toledo", "lat": 39.8628, "long": -4.0273}
  ],
  "skipped": [
    {"name": "Judah ibn Tibbon", "reason": "mentioned only by name"}
  ]
}
```

### Field notes

- `status`: `"extracted"`, or `"no_jewish_persons"` (then all lists are empty; keeps the entry from being re-processed).
- `times[].type`: `lifespan` (birth–death), `birth`, `death`, `activity` (floruit or dated activity); works use `composition`, `translation`, `revision`.
- `places[].type`: `birth`, `death`, `burial`, `residence`, `study`, `travel`, `activity`, `associated`.
- `relations[].type`: `influenced_by` (subject was influenced by target), `student_of`, `interlocutor_of` (correspondence, debate, polemic), `cites` (target is usually a work: `"target_kind": "works"`), `translated` (only when no specific translated work is extracted; otherwise use `works[].translators` + `translation_of`). `target_kind` defaults to `persons`.
- `works`: historical works only — no modern editions, translations or secondary literature. The bibliography's primary-literature section is a good place for alternate titles. Translations are their own work with `translators` and `translation_of`; commentaries use `commentary_on`.
- `authorship_status`: `authored`, `ascribed`, `questioned`, `translation`. `preservation_status`: only when stated, e.g. `lost`, `fragmentary`, `extant in manuscript`.
- `places[].lat/long`: decimal degrees for the city centre, only when you are confident; omit otherwise. Skip both for places that already have `db_id`.
- Keys are lowercase-hyphenated and unique within the file.
