import argparse
import json
import math
import re
import sys
from pathlib import Path

from common import (
    DEFAULT_EXPORT,
    ENTRIES_DIR,
    IDS_FILE,
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
SINGULAR_TIMES = ("lifespan", "birth", "death")
ENTITY_KINDS = ("persons", "works", "places")
LABEL_KEY = {"persons": "name", "works": "title", "places": "name"}
ALT_KEY = {"persons": "alt_names", "works": "alt_titles", "places": "alt_names"}
OUTPUT_ORDER = ("sources", "languages", "subjects", "places", "persons", "works")
NUMBERED_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")
MERGED_WORK_GAP = 100
COORDINATE_GAP_KM = 100


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
        self.db_ids = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return True
        ids = self.db_ids.get(ra, set()) | self.db_ids.get(rb, set())
        if len(ids) > 1:
            return False
        root, child = min(ra, rb), max(ra, rb)
        self.parent[child] = root
        self.db_ids[root] = ids
        return True


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
        self.created_ids = set(self.ids.values())
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
            if item.data.get("db_id"):
                uf.db_ids[item.ref] = {item.data["db_id"]}
        for item in items:
            for ref in item.data.get("same_as", []):
                target = self.local_ref(kind, item.entry, ref)
                if target and target[0] == "item" and not uf.union(item.ref, target[1]):
                    self.report.add("conflicting_same_as", f"{item.ref} -> {ref}: different db_ids")
            if item.data.get("db_id"):
                by_db.setdefault(item.data["db_id"], []).append(item.ref)
        for refs in by_db.values():
            for ref in refs[1:]:
                uf.union(refs[0], ref)
        for i, a in enumerate(items):
            for b in items[i + 1:]:
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
            return normalize(a.label) == normalize(b.label)
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
        imported = unique(self.ids[m.ref] for m in members if self.ids.get(m.ref) in self.db[kind])
        if len(imported) == 1 and not any(m.data.get("db_id") and m.data["db_id"] != imported[0] for m in members):
            return imported[0]
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
                evidenced = [m for m in members if m.data.get("jewish") is True and self.has_evidence(m.data.get("jewish_evidence") or {})]
                missing = [m.ref for m in members if m.data.get("jewish") is True] if not evidenced else []
                if missing:
                    self.report.add("errors", f"jewish without evidence quote: {missing}")
                self.emit["persons"].add(root)
            elif status == "uncertain":
                resolved = self.resolved.get(("persons", root))
                in_db = resolved[1] if resolved and resolved[0] == "existing" and resolved[1] not in self.created_ids else None
                if in_db:
                    self.emit["persons"].add(root)
                    self.report.add("uncertain_in_db_assumed_jewish", {"_id": in_db, "label": members[0].label})
                else:
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

    def has_evidence(self, evidence: dict) -> bool:
        external = evidence.get("external") or {}
        return bool(evidence.get("quote") or evidence.get("reason") or (external.get("url") and external.get("quote")))

    def external_source(self, external: dict) -> dict:
        name = external["source_name"].strip()
        source_id = next((d["_id"] for d in list(self.snapshot["sources"]) + list(self.new_docs["sources"].values()) if normalize(d["name"]) == normalize(name)), None)
        if source_id is None:
            source_id = self.allocate("source", f"sources:{normalize(name)}")
            root = re.match(r"^https?://[^/]+/", external["url"])
            doc = {"_id": source_id, "name": name}
            if root:
                doc["url"] = root.group(0)
            self.new_docs["sources"][source_id] = doc
            self.report.add("new_sources", name)
        return {"source": source_id, "url": external["url"]}

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
            if not isinstance(t.get("from"), int) and isinstance(t.get("until"), int):
                t = {**t, "from": t["until"], "estimated": True}
                t.pop("until")
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
        external = [(m.data.get("jewish_evidence") or {}).get("external") for m in members]
        external = [e for e in external if e and e.get("url") and e.get("quote") and e.get("source_name")]
        doc = {
            "name": main.label,
            "alt_names": alt_names,
            "sources": unique([self.entry_source(m.entry) for m in members] + [self.external_source(e) for e in external]),
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
        if jewish and external:
            notes = unique([f"Jewish identity ({e['source_name']}, {e['url']}): {e['quote']}" for e in external][:1] + notes)
        elif jewish:
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

    def element_key(self, field: str, element: dict, keys: tuple) -> tuple:
        return tuple(self.place_name(element[k]) if (field, k) == ("places", "place") else element.get(k) for k in keys)

    def merge_elements(self, kind: str, entity_id: str, field: str, current: list, incoming: list, keys: tuple, add: dict, element_sets: list):
        claimed = set()
        singular = {e["type"]: e for e in current if field == "times" and e["type"] in SINGULAR_TIMES}
        for item in incoming:
            key = self.element_key(field, item, keys)
            matches = [i for i, e in enumerate(current) if self.element_key(field, e, keys) == key]
            if any(current[i].get("source") == item["source"] and current[i].get("source_url") == item.get("source_url") for i in matches):
                continue
            unsourced = [i for i in matches if "source" not in current[i] and i not in claimed]
            if unsourced:
                i = unsourced[0]
                claimed.add(i)
                values = {k: item[k] for k in ("source", "source_url") if k in item}
                for extra in ("description", "estimated", "until"):
                    if extra in item and extra not in current[i] and extra not in keys:
                        values[extra] = item[extra]
                match = {k: current[i].get(k) for k in keys}
                element_sets.append({"field": field, "match": match, "set": values})
                continue
            if not matches and item.get("type") in singular:
                other = singular[item["type"]]
                self.report.add("conflicting_values_added", {"collection": kind, "_id": entity_id, "field": f"{field}.{item['type']}", "db": [other["from"], other.get("until")], "sep": [item["from"], item.get("until")], "sep_url": item.get("source_url")})
            add.setdefault(field, []).append(item)

    def place_name(self, place_id: str) -> str:
        doc = self.db["places"].get(place_id) or self.new_docs["places"].get(place_id)
        return normalize(re.sub(r"\s*\(.*$", "", doc["name"])) if doc else place_id

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
        element_sets = []
        if "times" in doc:
            self.merge_elements(kind, entity_id, "times", existing.get("times", []), doc["times"], ("type", "from", "until"), add, element_sets)
        if kind == "persons":
            self.merge_elements(kind, entity_id, "places", existing.get("places", []), doc["places"], ("place", "type", "from"), add, element_sets)
            self.merge_elements(kind, entity_id, "relations", existing.get("relations", []), doc["relations"], ("type", "target"), add, element_sets)
        for field in ("description", "authorship_status", "preservation_status", "translation_of", "commentary_on", "location"):
            if field in doc and field not in existing:
                set_missing[field] = doc[field]
            elif field == "description" and field in doc and normalize(existing[field]) != normalize(doc[field]):
                url = doc["sources"][0]["url"] if doc.get("sources") else SEP_URL
                note = f"SEP ({url}): {doc[field]}"
                if note not in existing.get("notes", []):
                    add.setdefault("notes", []).append(note)
            elif field in doc and existing.get(field) != doc[field] and field != "location":
                self.report.add("kept_existing_values", {"collection": kind, "_id": entity_id, "field": field, "db": existing[field], "sep": doc[field]})
        if add or set_missing or element_sets:
            update = {"collection": kind, "_id": entity_id, "label": existing[label_field]}
            if add:
                update["add_to_set"] = add
            if set_missing:
                update["set_if_missing"] = set_missing
            if element_sets:
                update["set_element_fields"] = element_sets
            self.updates[(kind, entity_id)] = update
            merged = {k: (list(v) if isinstance(v, list) else v) for k, v in existing.items()}
            for change in element_sets:
                for i, element in enumerate(merged[change["field"]]):
                    if all(element.get(k) == v for k, v in change["match"].items()) and "source" not in element:
                        merged[change["field"]][i] = {**element, **change["set"]}
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
                else:
                    self.merge_existing(kind, entity_id, doc)
        for kind, docs in self.new_docs.items():
            for doc in docs.values():
                for error in validate(doc, COLLECTIONS[kind]):
                    self.report.add("validation_errors", f"new {kind} {doc['_id']}: {error}")

    def distance_km(self, a: list, b: list) -> float:
        lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
        h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        return 6371 * 2 * math.asin(math.sqrt(h))

    def db_cleanup(self, notes_path: Path) -> dict:
        used = set()
        for update in self.updates.values():
            used.add(update["_id"])
        for docs in self.new_docs.values():
            used |= set(re.findall(r"(?:person|work|place)_[a-z0-9]{8}", json.dumps(list(docs.values()))))
        person_span = {d["_id"]: span(d.get("times", []) + d.get("places", [])) for d in self.snapshot["persons"]}
        cleanup = {"duplicate_records": [], "suspected_merged_works": [], "suspect_coordinates": [], "conflicting_dates": self.report.sections.get("conflicting_values_added", [])}
        for kind in ENTITY_KINDS:
            uf = UnionFind()
            by_variant = {}
            for doc in self.snapshot[kind]:
                labels = [NUMBERED_SUFFIX.sub("", doc_label(kind, doc) or "")] + doc_alt_labels(kind, doc)
                if kind == "places":
                    labels = [re.sub(r"\s*\(.*$", "", l) for l in labels]
                for v in variants(*labels):
                    by_variant.setdefault(v, []).append(doc["_id"])
            for ids in by_variant.values():
                for a in ids:
                    for b in ids:
                        if a >= b:
                            continue
                        if kind == "persons" and not spans_compatible(person_span[a], person_span[b]):
                            continue
                        if kind == "works":
                            aa, ab = set(self.db["works"][a].get("authors", [])), set(self.db["works"][b].get("authors", []))
                            names_a = {n for x in aa if x in self.db["persons"] for n in variants(self.db["persons"][x]["name"])}
                            names_b = {n for x in ab if x in self.db["persons"] for n in variants(self.db["persons"][x]["name"])}
                            if aa and ab and not (aa & ab) and not (names_a & names_b):
                                continue
                            wa, wb = self.db["works"][a], self.db["works"][b]
                            if wa.get("translation_of") and wb.get("translation_of") and wa["translation_of"] != wb["translation_of"]:
                                continue
                            if wa.get("translators") and wb.get("translators") and not set(wa["translators"]) & set(wb["translators"]):
                                continue
                            if not aa and not ab and not (wa.get("translation_of") or wa.get("translators")) and not (wb.get("translation_of") or wb.get("translators")):
                                continue
                        uf.union(a, b)
            groups = {}
            for doc in self.snapshot[kind]:
                groups.setdefault(uf.find(doc["_id"]), []).append(doc["_id"])
            for ids in groups.values():
                if len(ids) > 1:
                    numbered = sum(1 for i in ids if NUMBERED_SUFFIX.search(doc_label(kind, self.db[kind][i]) or ""))
                    cleanup["duplicate_records"].append({
                        "collection": kind,
                        "kind": "numbered_variants_maybe_intentional" if numbered == len(ids) else "duplicate",
                        "records": [{"_id": i, "label": doc_label(kind, self.db[kind][i]), "coordinates": self.db[kind][i].get("location", {}).get("coordinates") if kind == "places" else None} for i in ids],
                        "touched_by_sep_import": sorted(set(ids) & used),
                    })
                    if kind == "places":
                        coords = [(i, self.db["places"][i]["location"]["coordinates"]) for i in ids if self.db["places"][i].get("location")]
                        far = [(a, b) for x, (a, ca) in enumerate(coords) for b, cb in coords[x + 1:] if self.distance_km(ca, cb) > COORDINATE_GAP_KM]
                        if far:
                            cleanup["suspect_coordinates"].append({"label": doc_label(kind, self.db[kind][ids[0]]), "pairs_over_100km": far})
        for doc in self.snapshot["works"]:
            spans = [(a, person_span.get(a)) for a in doc.get("authors", []) if person_span.get(a)]
            for x, (a, sa) in enumerate(spans):
                for b, sb in spans[x + 1:]:
                    if sa[0] - MERGED_WORK_GAP > sb[1] or sb[0] - MERGED_WORK_GAP > sa[1]:
                        cleanup["suspected_merged_works"].append({"_id": doc["_id"], "title": doc["title"], "authors": [self.db["persons"][i]["name"] for i in doc["authors"] if i in self.db["persons"]]})
                        break
                else:
                    continue
                break
        cleanup["noted_during_extraction"] = load_json(notes_path) if notes_path.exists() else []
        return cleanup

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
    parser.add_argument("--ids", type=Path, default=IDS_FILE)
    parser.add_argument("--cleanup-notes", type=Path, default=WORK_DIR / "db_cleanup_notes.json")
    args = parser.parse_args()

    assembler = Assembler(load_snapshot(args.snapshot), load_extractions(args.entries), args.export, args.ids)
    assembler.run()

    args.out.mkdir(parents=True, exist_ok=True)
    for collection in OUTPUT_ORDER:
        docs = sorted(assembler.new_docs[collection].values(), key=lambda d: d["_id"])
        (args.out / f"{collection}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    updates = [assembler.updates[k] for k in sorted(assembler.updates)]
    (args.out / "updates.json").write_text(json.dumps(updates, ensure_ascii=False, indent=2), encoding="utf-8")
    assembler.report.sections["db_cleanup"] = assembler.db_cleanup(args.cleanup_notes)
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
