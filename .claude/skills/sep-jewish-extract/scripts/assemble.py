import argparse
import json
import re
import sys
from pathlib import Path

from common import (
    DEFAULT_EXPORT,
    ENTRIES_DIR,
    REPO,
    SNAPSHOT,
    WORK_DIR,
    doc_alt_labels,
    doc_label,
    load_extractions,
    load_json,
    load_snapshot,
    normalize,
    similar_normalized,
    span,
    spans_compatible,
    variants,
)

sys.path.insert(0, str(REPO / "backend"))

from app.core.db_schema import COLLECTIONS, COLLECTION_PREFIXES, ID_LENGTH, new_id

SEP_NAME = "Stanford Encyclopedia of Philosophy"
SEP_URL = "https://plato.stanford.edu/"
ID_PATTERN = re.compile(rf"^({'|'.join(COLLECTION_PREFIXES.values())})_[a-z0-9]{{{ID_LENGTH}}}$")
SECTION_NUMBER = re.compile(r"^[\dA-Z]+(\.\d+)*\.?\s+")
NEAR_DUPLICATE = 0.88
ENTITY_KINDS = ("persons", "works", "places")
LABEL_KEY = {"persons": "name", "works": "title", "places": "name"}
ALT_KEY = {"persons": "alt_names", "works": "alt_titles", "places": "alt_names"}
OUTPUT_ORDER = ("sources", "languages", "subjects", "places", "persons", "works")


class Report:
    def __init__(self):
        self.sections = {}

    def add(self, section: str, item):
        self.sections.setdefault(section, []).append(item)


class Item:
    def __init__(self, kind: str, entry: str, data: dict):
        self.kind = kind
        self.entry = entry
        self.data = data
        self.ref = f"{entry}/{data['key']}"
        self.label = data.get(LABEL_KEY[kind]) or data["key"]
        self.variants = variants(self.label, *data.get(ALT_KEY[kind], []))


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def bson_type_ok(value, bson_type: str) -> bool:
    return {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "double": lambda v: isinstance(v, float),
        "bool": lambda v: isinstance(v, bool),
    }[bson_type](value)


def validate(value, schema: dict, path: str = "") -> list:
    errors = []
    if "bsonType" in schema and not bson_type_ok(value, schema["bsonType"]):
        return [f"{path or '/'}: expected {schema['bsonType']}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if "pattern" in schema and not re.search(schema["pattern"], value):
        errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required")
        for key, sub in value.items():
            if key in schema.get("properties", {}):
                errors += validate(sub, schema["properties"][key], f"{path}.{key}")
            elif "properties" in schema:
                errors.append(f"{path}.{key}: not in schema")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            errors.append(f"{path}: wrong number of items")
        for i, sub in enumerate(value):
            errors += validate(sub, schema.get("items", {}), f"{path}[{i}]")
    return errors


def unique(values) -> list:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


class Assembler:
    def __init__(self, snapshot: dict, extractions: dict, export: Path, ids_path: Path):
        self.snapshot = snapshot
        self.extractions = extractions
        self.export = export
        self.ids_path = ids_path
        self.ids = load_json(ids_path) if ids_path.exists() else {}
        self.used_ids = {d["_id"] for c in COLLECTIONS for d in snapshot[c]} | set(self.ids.values())
        self.db = {c: {d["_id"]: d for d in snapshot[c]} for c in COLLECTIONS}
        self.db_labels = {
            kind: [
                (d["_id"], [normalize(l) for l in [doc_label(kind, d) or ""] + doc_alt_labels(kind, d)], variants(doc_label(kind, d) or "", *doc_alt_labels(kind, d)), span(d.get("times", []) + d.get("places", [])))
                for d in snapshot[kind]
            ]
            for kind in ENTITY_KINDS
        }
        self.report = Report()
        self.entries = {}
        self.items = {kind: {} for kind in ENTITY_KINDS}
        self.groups = {kind: {} for kind in ENTITY_KINDS}
        self.group_of = {}
        self.resolved = {}
        self.new_docs = {c: {} for c in COLLECTIONS}
        self.updates = {}

    def allocate(self, prefix: str, key: str) -> str:
        if key in self.ids:
            return self.ids[key]
        entity_id = new_id(prefix)
        while entity_id in self.used_ids:
            entity_id = new_id(prefix)
        self.used_ids.add(entity_id)
        self.ids[key] = entity_id
        return entity_id

    def load_entries(self):
        for entry, extraction in self.extractions.items():
            path = self.export / "json" / f"{entry}.json"
            if not path.exists():
                self.report.add("errors", f"{entry}: no export file {path}")
                continue
            sep = load_json(path)
            anchors = {}
            for item in sep["toc"]:
                anchors[normalize(item["title"])] = item["anchor"]
                anchors[normalize(SECTION_NUMBER.sub("", item["title"]))] = item["anchor"]
            supplements = {}
            for supplement in sep["supplements"]:
                supplements[normalize(supplement["file"])] = supplement["url"]
                if supplement["title"]:
                    supplements[normalize(supplement["title"])] = supplement["url"]
            self.entries[entry] = {"url": sep["url"], "anchors": anchors, "supplements": supplements}
            for kind in ENTITY_KINDS:
                for data in extraction.get(kind, []):
                    item = Item(kind, entry, data)
                    if item.ref in self.items[kind]:
                        self.report.add("errors", f"duplicate key {item.ref}")
                    self.items[kind][item.ref] = item

    def section_url(self, entry: str, section: str | None) -> str:
        info = self.entries[entry]
        url = info["url"]
        if not section or normalize(section) in ("preamble", "introduction"):
            return url
        key = normalize(section)
        if key == "notes":
            return url + "notes.html"
        if key in ("bibliography", "primary literature", "secondary literature"):
            return url + "#Bib"
        if key in info["supplements"]:
            return info["supplements"][key]
        for candidate in (key, normalize(SECTION_NUMBER.sub("", section))):
            if candidate in info["anchors"]:
                return f"{url}#{info['anchors'][candidate]}"
        self.report.add("unknown_sections", f"{entry}: {section!r}")
        return url

    def entry_source(self, entry: str) -> dict:
        return {"source": self.sep_id, "url": self.entries[entry]["url"]}

    def resolve_sep_source(self):
        for doc in self.snapshot["sources"]:
            if normalize(doc["name"]) == normalize(SEP_NAME) or "plato.stanford.edu" in doc.get("url", ""):
                self.sep_id = doc["_id"]
                return
        self.sep_id = self.allocate("source", "source:sep")
        self.new_docs["sources"][self.sep_id] = {"_id": self.sep_id, "name": SEP_NAME, "url": SEP_URL}

    def item_span(self, item: Item):
        return span(item.data.get("times", []) + item.data.get("places", []))

    def local_ref(self, kind: str, entry: str, ref):
        if not isinstance(ref, str):
            return None
        if ID_PATTERN.match(ref):
            return ("db", ref)
        if ref.startswith("sep:"):
            return ("item", ref[4:]) if ref[4:] in self.items[kind] else None
        if ref.startswith("name:"):
            return ("name", ref[5:])
        full = f"{entry}/{ref}"
        return ("item", full) if full in self.items[kind] else None

    def group_items(self, kind: str):
        uf = UnionFind()
        items = list(self.items[kind].values())
        by_db = {}
        for item in items:
            uf.find(item.ref)
            for ref in item.data.get("same_as", []):
                target = self.local_ref(kind, item.entry, ref)
                if target and target[0] == "item":
                    uf.union(item.ref, target[1])
            if item.data.get("db_id"):
                by_db.setdefault(item.data["db_id"], []).append(item.ref)
        for refs in by_db.values():
            for ref in refs[1:]:
                uf.union(refs[0], ref)
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a.data.get("db_id") and b.data.get("db_id") and a.data["db_id"] != b.data["db_id"]:
                    continue
                if not (a.variants & b.variants):
                    continue
                if kind == "persons" and not spans_compatible(self.item_span(a), self.item_span(b)):
                    continue
                if kind == "works" and not self.works_share_author(a, b):
                    continue
                uf.union(a.ref, b.ref)
        groups = {}
        for item in items:
            groups.setdefault(uf.find(item.ref), []).append(item)
        self.groups[kind] = groups
        for root, members in groups.items():
            for member in members:
                self.group_of[(kind, member.ref)] = root

    def person_key(self, entry: str, ref):
        target = self.local_ref("persons", entry, ref)
        if target is None:
            return None
        if target[0] == "item":
            return self.group_of.get(("persons", target[1]))
        return target

    def works_share_author(self, a: Item, b: Item) -> bool:
        authors_a = {self.person_key(a.entry, r) for r in a.data.get("authors", [])} - {None}
        authors_b = {self.person_key(b.entry, r) for r in b.data.get("authors", [])} - {None}
        if not authors_a or not authors_b:
            return True
        if authors_a & authors_b:
            return True
        names_a = {n for k in authors_a for n in self.key_variants(k)}
        names_b = {n for k in authors_b for n in self.key_variants(k)}
        return bool(names_a & names_b)

    def key_variants(self, key) -> set:
        if isinstance(key, tuple):
            if key[0] == "db" and key[1] in self.db["persons"]:
                doc = self.db["persons"][key[1]]
                return variants(doc["name"], *doc.get("alt_names", []))
            if key[0] == "name":
                return variants(key[1])
            return set()
        return {v for m in self.groups["persons"].get(key, []) for v in m.variants}

    def match_db(self, kind: str, root: str, members: list):
        explicit = unique(m.data["db_id"] for m in members if m.data.get("db_id"))
        for db_id in explicit:
            if db_id not in self.db[kind]:
                self.report.add("unresolved", {"kind": kind, "group": root, "reason": f"db_id {db_id} not in snapshot"})
                return "unresolved"
        if len(explicit) > 1:
            self.report.add("unresolved", {"kind": kind, "group": root, "reason": f"conflicting db_ids {explicit}"})
            return "unresolved"
        if explicit:
            return explicit[0]
        names = {v for m in members for v in m.variants}
        group_span = span([t for m in members for t in m.data.get("times", []) + m.data.get("places", [])])
        group_authors = self.group_author_ids(members) if kind == "works" else set()
        exact, near = [], []
        for db_id, labels, db_variants, db_span in self.db_labels[kind]:
            if kind == "persons" and not spans_compatible(group_span, db_span):
                continue
            if kind == "works" and group_authors and self.db[kind][db_id].get("authors") and not group_authors & set(self.db[kind][db_id]["authors"]):
                continue
            if names & db_variants:
                exact.append(db_id)
            elif any(similar_normalized(name, label, NEAR_DUPLICATE) for name in names for label in labels):
                near.append(db_id)
        confirmed_new = any(m.data.get("confirmed_new") for m in members)
        if len(exact) == 1 and not confirmed_new:
            return exact[0]
        if len(exact) > 1 and not confirmed_new:
            self.report.add("unresolved", {"kind": kind, "group": root, "label": members[0].label, "reason": "several DB matches", "candidates": self.describe(kind, exact)})
            return "unresolved"
        if near and not confirmed_new:
            self.report.add("unresolved", {"kind": kind, "group": root, "label": members[0].label, "reason": "possible DB duplicates; set db_id or confirmed_new", "candidates": self.describe(kind, near)})
            return "unresolved"
        return None

    def group_author_ids(self, members: list) -> set:
        ids = set()
        for m in members:
            for r in m.data.get("authors", []):
                key = self.person_key(m.entry, r)
                if isinstance(key, tuple) and key[0] == "db":
                    ids.add(key[1])
                elif isinstance(key, str) and self.resolved.get(("persons", key)):
                    ids.add(self.resolved[("persons", key)][1])
        return ids

    def describe(self, kind: str, ids: list) -> list:
        return [f"{i}: {doc_label(kind, self.db[kind][i])}" for i in ids]

    def resolve_groups(self, kind: str):
        prefix = COLLECTION_PREFIXES[kind]
        taken = set()
        for root, members in self.groups[kind].items():
            match = self.match_db(kind, root, members)
            if match == "unresolved":
                self.resolved[(kind, root)] = None
                continue
            if match:
                self.resolved[(kind, root)] = ("existing", match)
                continue
            existing = [self.ids[m.ref] for m in sorted(members, key=lambda m: m.ref) if m.ref in self.ids and self.ids[m.ref] not in taken]
            if existing:
                entity_id = existing[0]
            else:
                for member in members:
                    self.ids.pop(member.ref, None)
                entity_id = self.allocate(prefix, sorted(m.ref for m in members)[0])
            taken.add(entity_id)
            for member in members:
                self.ids[member.ref] = entity_id
            self.resolved[(kind, root)] = ("new", entity_id)

    def ref_id(self, kind: str, entry: str, ref, context: str):
        target = self.local_ref(kind, entry, ref)
        if target is None:
            self.report.add("dropped_refs", f"{context}: unknown {kind} reference {ref!r}")
            return None
        if target[0] == "db":
            if target[1] not in self.db[kind]:
                self.report.add("dropped_refs", f"{context}: {target[1]} not in snapshot")
                return None
            return target[1]
        if target[0] == "item":
            resolved = self.resolved.get((kind, self.group_of[(kind, target[1])]))
            if resolved is None or not self.emitted(kind, self.group_of[(kind, target[1])]):
                self.report.add("dropped_refs", f"{context}: {ref!r} is unresolved or not emitted")
                return None
            return resolved[1]
        matches = [root for root, members in self.groups[kind].items() if variants(target[1]) & {v for m in members for v in m.variants}]
        db_matches = [d["_id"] for d in self.snapshot[kind] if variants(target[1]) & variants(doc_label(kind, d) or "", *doc_alt_labels(kind, d))]
        candidates = unique([self.resolved[(kind, r)][1] for r in matches if self.resolved.get((kind, r)) and self.emitted(kind, r)] + db_matches)
        if len(candidates) == 1:
            return candidates[0]
        self.report.add("dropped_refs", f"{context}: name reference {ref!r} matched {len(candidates)} records")
        return None

    def jewish_status(self, members: list):
        values = [m.data.get("jewish") for m in members]
        if True in values:
            return True
        if "uncertain" in values:
            return "uncertain"
        return False

    def compute_emission(self):
        self.emit = {kind: set() for kind in ENTITY_KINDS}
        for root, members in self.groups["persons"].items():
            status = self.jewish_status(members)
            if status is True:
                missing = [m.ref for m in members if m.data.get("jewish") is True and not ((m.data.get("jewish_evidence") or {}).get("quote") or (m.data.get("jewish_evidence") or {}).get("reason"))]
                if missing:
                    self.report.add("errors", f"jewish without evidence quote: {missing}")
                self.emit["persons"].add(root)
            elif status == "uncertain":
                self.report.add("review_uncertain_jewish", {"group": root, "label": members[0].label, "notes": [m.data.get("jewish_evidence") for m in members]})
        jewish = set(self.emit["persons"])
        jewish_ids = {("db", self.resolved[("persons", root)][1]) for root in jewish if self.resolved.get(("persons", root))}
        changed = True
        while changed:
            changed = False
            for root, members in self.groups["works"].items():
                if root in self.emit["works"]:
                    continue
                people = {self.person_key(m.entry, r) for m in members for r in m.data.get("authors", []) + m.data.get("translators", [])}
                if people & jewish or people & jewish_ids:
                    self.emit["works"].add(root)
                    changed = True
            for root in list(self.emit["works"]):
                for m in self.groups["works"][root]:
                    for field in ("translation_of", "commentary_on"):
                        changed |= self.emit_work_ref(m.entry, m.data.get(field))
            for root, members in self.groups["works"].items():
                if root not in self.emit["works"]:
                    continue
                for m in members:
                    for r in m.data.get("authors", []):
                        key = self.person_key(m.entry, r)
                        if isinstance(key, str) and key not in self.emit["persons"]:
                            self.emit["persons"].add(key)
                            changed = True
            for root in list(self.emit["persons"]):
                if root not in jewish:
                    continue
                for m in self.groups["persons"][root]:
                    for relation in m.data.get("relations", []):
                        if relation.get("target_kind", "persons") == "works":
                            changed |= self.emit_work_ref(m.entry, relation.get("target"))
                            continue
                        key = self.person_key(m.entry, relation["target"])
                        if isinstance(key, str) and key not in self.emit["persons"]:
                            self.emit["persons"].add(key)
                            changed = True
        for root in jewish:
            for m in self.groups["persons"][root]:
                for place in m.data.get("places", []):
                    target = self.local_ref("places", m.entry, place.get("place"))
                    if target and target[0] == "item":
                        self.emit["places"].add(self.group_of[("places", target[1])])
        self.non_jewish = self.emit["persons"] - jewish

    def emit_work_ref(self, entry: str, ref) -> bool:
        target = self.local_ref("works", entry, ref)
        if not target or target[0] != "item":
            return False
        root = self.group_of[("works", target[1])]
        if root in self.emit["works"]:
            return False
        self.emit["works"].add(root)
        return True

    def emitted(self, kind: str, root: str) -> bool:
        return root in self.emit[kind]

    def resolve_named(self, collection: str, names: list, entry: str) -> list:
        ids = []
        for name in names:
            key = normalize(name)
            match = next((d["_id"] for d in self.snapshot[collection] if normalize(d["name"]) == key), None)
            if match is None:
                match = next((d["_id"] for d in self.new_docs[collection].values() if normalize(d["name"]) == key), None)
            if match is None:
                match = self.allocate(COLLECTION_PREFIXES[collection], f"{collection}:{key}")
                doc = {"_id": match, "name": name.strip()}
                if collection == "subjects":
                    doc["sources"] = [self.entry_source(entry)]
                self.new_docs[collection][match] = doc
                self.report.add(f"new_{collection}", name.strip())
            ids.append(match)
        return unique(ids)

    def provenance(self, entry: str, record: dict) -> dict:
        return {"source": self.sep_id, "source_url": self.section_url(entry, record.get("section"))}

    def time_records(self, member: Item, context: str) -> list:
        times = []
        for t in member.data.get("times", []):
            if not isinstance(t.get("from"), int) or not t.get("type"):
                self.report.add("dropped_data", f"{context}: time without type/int from {t}")
                continue
            record = {"type": t["type"], "from": t["from"]}
            if isinstance(t.get("until"), int):
                record["until"] = t["until"]
            if t.get("estimated"):
                record["estimated"] = True
            if t.get("description"):
                record["description"] = t["description"]
            record.update(self.provenance(member.entry, t))
            times.append(record)
        return times

    def place_records(self, member: Item, context: str) -> list:
        places = []
        for p in member.data.get("places", []):
            place_id = self.ref_id("places", member.entry, p.get("place"), context)
            if place_id is None or not p.get("type"):
                continue
            record = {"place": place_id, "type": p["type"]}
            for key in ("from", "until"):
                if isinstance(p.get(key), int):
                    record[key] = p[key]
            if p.get("estimated"):
                record["estimated"] = True
            if p.get("description"):
                record["description"] = p["description"]
            record.update(self.provenance(member.entry, p))
            places.append(record)
        return places

    def relation_records(self, member: Item, context: str) -> list:
        relations = []
        for r in member.data.get("relations", []):
            target_kind = r.get("target_kind", "persons")
            target = self.ref_id(target_kind, member.entry, r.get("target"), context)
            if target is None:
                continue
            record = {"type": r["type"], "target": target}
            if r.get("description"):
                record["description"] = r["description"]
            record.update(self.provenance(member.entry, r))
            relations.append(record)
        return relations

    def preferred(self, members: list) -> Item:
        return sorted(members, key=lambda m: (not m.data.get("entry_subject"), -len(json.dumps(m.data))))[0]

    def build_place(self, root: str, members: list) -> dict:
        main = self.preferred(members)
        doc = {"name": main.label, "sources": unique(self.entry_source(m.entry) for m in members)}
        coords = next(((m.data["lat"], m.data["long"]) for m in members if isinstance(m.data.get("lat"), (int, float)) and isinstance(m.data.get("long"), (int, float))), None)
        if coords:
            doc["location"] = {"type": "Point", "coordinates": [float(coords[1]), float(coords[0])]}
        return doc

    def build_person(self, root: str, members: list) -> dict:
        main = self.preferred(members)
        context = f"person {main.label}"
        jewish = root not in self.non_jewish
        alt_names = unique(n for m in members for n in [m.label] + m.data.get("alt_names", []) if n != main.label)
        doc = {
            "name": main.label,
            "alt_names": alt_names,
            "sources": unique(self.entry_source(m.entry) for m in members),
            "subjects": self.resolve_named("subjects", unique(s for m in members for s in m.data.get("subjects", [])), main.entry) if jewish else [],
            "languages": self.resolve_named("languages", unique(s for m in members for s in m.data.get("languages", [])), main.entry) if jewish else [],
            "times": self.dedupe_times([t for m in members for t in self.time_records(m, context)]),
            "places": self.dedupe_places([p for m in members for p in self.place_records(m, context)]) if jewish else [],
            "relations": self.dedupe_relations([r for m in members for r in self.relation_records(m, context)]) if jewish else [],
        }
        description = main.data.get("description") or next((m.data["description"] for m in members if m.data.get("description")), None)
        if description:
            doc["description"] = description
        notes = unique(n for m in members for n in m.data.get("notes", []))
        if jewish:
            notes = unique([f"Jewish identity ({m.data['jewish_evidence'].get('section') or 'preamble'}, {self.entries[m.entry]['url']}): {m.data['jewish_evidence']['quote']}" for m in members if m.data.get("jewish") is True and (m.data.get("jewish_evidence") or {}).get("quote")][:1] + notes)
        if notes:
            doc["notes"] = notes
        return doc

    def build_work(self, root: str, members: list) -> dict:
        main = self.preferred(members)
        context = f"work {main.label}"
        doc = {
            "title": main.label,
            "alt_titles": unique(t for m in members for t in [m.label] + m.data.get("alt_titles", []) if t != main.label),
            "sources": unique(self.entry_source(m.entry) for m in members),
            "subjects": self.resolve_named("subjects", unique(s for m in members for s in m.data.get("subjects", [])), main.entry),
            "languages": self.resolve_named("languages", unique(s for m in members for s in m.data.get("languages", [])), main.entry),
            "authors": unique(i for m in members for r in m.data.get("authors", []) if (i := self.ref_id("persons", m.entry, r, context))),
            "translators": unique(i for m in members for r in m.data.get("translators", []) if (i := self.ref_id("persons", m.entry, r, context))),
            "times": self.dedupe_times([t for m in members for t in self.time_records(m, context)]),
        }
        if not doc["alt_titles"]:
            del doc["alt_titles"]
        if not doc["times"]:
            del doc["times"]
        for field in ("description", "authorship_status", "preservation_status"):
            value = main.data.get(field) or next((m.data[field] for m in members if m.data.get(field)), None)
            if value:
                doc[field] = value
        for field in ("translation_of", "commentary_on"):
            for m in members:
                if m.data.get(field):
                    target = self.ref_id("works", m.entry, m.data[field], context)
                    if target:
                        doc[field] = target
                        break
        return doc

    def dedupe_times(self, times: list) -> list:
        seen, result = set(), []
        for t in sorted(times, key=lambda t: t["from"]):
            key = (t["type"], t["from"], t.get("until"))
            if key not in seen:
                seen.add(key)
                result.append(t)
        return result

    def dedupe_places(self, places: list) -> list:
        seen, result = set(), []
        for p in sorted(places, key=lambda p: (p.get("from") is None, p.get("from", 0))):
            key = (p["place"], p["type"], p.get("from"), p.get("until"))
            if key not in seen:
                seen.add(key)
                result.append(p)
        return result

    def dedupe_relations(self, relations: list) -> list:
        seen, result = set(), []
        for r in relations:
            if (r["type"], r["target"]) not in seen:
                seen.add((r["type"], r["target"]))
                result.append(r)
        return result

    def merge_existing(self, kind: str, entity_id: str, doc: dict):
        existing = self.db[kind][entity_id]
        add, set_missing = {}, {}
        label_field = "title" if kind == "works" else "name"
        alt_field = "alt_titles" if kind == "works" else "alt_names"
        known_labels = {normalize(existing[label_field])} | {normalize(a) for a in existing.get(alt_field, [])}
        if kind != "places":
            new_alts = [a for a in [doc[label_field]] + doc.get(alt_field, []) if normalize(a) not in known_labels]
            if new_alts:
                add[alt_field] = unique(new_alts)
        existing_sources = {(s["source"], s.get("url")) for s in existing.get("sources", [])}
        new_sources = [s for s in doc.get("sources", []) if (s["source"], s.get("url")) not in existing_sources]
        if new_sources:
            add["sources"] = new_sources
        for field in ("subjects", "languages", "authors", "translators", "notes"):
            values = [v for v in doc.get(field, []) if v not in existing.get(field, [])]
            if values:
                add[field] = values
        if "times" in doc:
            keys = {(t["type"], t["from"], t.get("until")) for t in existing.get("times", [])}
            values = [t for t in doc["times"] if (t["type"], t["from"], t.get("until")) not in keys]
            if values:
                add["times"] = values
        if kind == "persons":
            keys = {(p["place"], p["type"], p.get("from")) for p in existing.get("places", [])}
            values = [p for p in doc["places"] if (p["place"], p["type"], p.get("from")) not in keys]
            if values:
                add["places"] = values
            keys = {(r["type"], r["target"]) for r in existing.get("relations", [])}
            values = [r for r in doc["relations"] if (r["type"], r["target"]) not in keys]
            if values:
                add["relations"] = values
        for field in ("description", "authorship_status", "preservation_status", "translation_of", "commentary_on", "location"):
            if field in doc and field not in existing:
                set_missing[field] = doc[field]
            elif field in doc and existing.get(field) != doc[field] and field != "location":
                self.report.add("kept_existing_values", {"collection": kind, "_id": entity_id, "field": field, "db": existing[field], "sep": doc[field]})
        if add or set_missing:
            update = {"collection": kind, "_id": entity_id, "label": existing[label_field]}
            if add:
                update["add_to_set"] = add
            if set_missing:
                update["set_if_missing"] = set_missing
            self.updates[(kind, entity_id)] = update
            merged = dict(existing)
            for field, values in add.items():
                merged[field] = merged.get(field, []) + values
            merged.update(set_missing)
            for error in validate(merged, COLLECTIONS[kind]):
                self.report.add("validation_errors", f"update {kind} {entity_id}: {error}")

    def build_all(self):
        for kind, builder in (("places", self.build_place), ("persons", self.build_person), ("works", self.build_work)):
            for root, members in self.groups[kind].items():
                if root not in self.emit[kind] or self.resolved.get((kind, root)) is None:
                    continue
                state, entity_id = self.resolved[(kind, root)]
                doc = builder(root, members)
                if state == "new":
                    self.new_docs[kind][entity_id] = {"_id": entity_id, **doc}
                elif kind == "persons" and root in self.non_jewish:
                    continue
                else:
                    self.merge_existing(kind, entity_id, doc)
        for kind, docs in self.new_docs.items():
            for doc in docs.values():
                for error in validate(doc, COLLECTIONS[kind]):
                    self.report.add("validation_errors", f"new {kind} {doc['_id']}: {error}")

    def run(self):
        self.load_entries()
        self.resolve_sep_source()
        for kind in ENTITY_KINDS:
            self.group_items(kind)
        for kind in ENTITY_KINDS:
            self.resolve_groups(kind)
        self.compute_emission()
        self.build_all()
        for kind, groups in self.groups.items():
            merged = [[m.ref for m in members] for members in groups.values() if len(members) > 1]
            for refs in merged:
                self.report.add(f"merged_{kind}", refs)
        for entry, extraction in self.extractions.items():
            for skipped in extraction.get("skipped", []):
                self.report.add("skipped_by_extractor", {"entry": entry, **skipped})


def main():
    parser = argparse.ArgumentParser(description="Assemble SEP extractions into MongoDB-ready JSON for the jephy database.")
    parser.add_argument("--entries", type=Path, default=ENTRIES_DIR)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--out", type=Path, default=WORK_DIR / "out")
    parser.add_argument("--ids", type=Path, default=WORK_DIR / "ids.json")
    args = parser.parse_args()

    assembler = Assembler(load_snapshot(args.snapshot), load_extractions(args.entries), args.export, args.ids)
    assembler.run()

    args.out.mkdir(parents=True, exist_ok=True)
    for collection in OUTPUT_ORDER:
        docs = sorted(assembler.new_docs[collection].values(), key=lambda d: d["_id"])
        (args.out / f"{collection}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    updates = [assembler.updates[k] for k in sorted(assembler.updates)]
    (args.out / "updates.json").write_text(json.dumps(updates, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "report.json").write_text(json.dumps(assembler.report.sections, ensure_ascii=False, indent=2), encoding="utf-8")
    args.ids.write_text(json.dumps(assembler.ids, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    print(f"entries: {len(assembler.entries)}")
    for collection in OUTPUT_ORDER:
        print(f"new {collection}: {len(assembler.new_docs[collection])}")
    print(f"updates to existing records: {len(updates)}")
    for section, items in assembler.report.sections.items():
        print(f"report {section}: {len(items)}")
    print(f"written {args.out}")


if __name__ == "__main__":
    main()
