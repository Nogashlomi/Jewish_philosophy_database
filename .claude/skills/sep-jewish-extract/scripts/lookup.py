import argparse
from pathlib import Path

from common import ENTRIES_DIR, SNAPSHOT, doc_alt_labels, doc_label, load_extractions, load_snapshot, normalize, similarity, span, variants

COLLECTIONS = ("persons", "works", "places", "subjects", "languages", "sources")
EXTRACTION_KEYS = {"persons": "name", "works": "title", "places": "name"}


def score(query: str, labels: list) -> float:
    query_variants = variants(query)
    if query_variants & variants(*labels):
        return 1.0
    return max((similarity(query, label) for label in labels), default=0.0)


def describe_db(collection: str, doc: dict, snapshot_names: dict) -> str:
    parts = [doc["_id"], doc_label(collection, doc)]
    alts = doc_alt_labels(collection, doc)
    if alts:
        parts.append(f"alt: {'; '.join(alts)}")
    if collection == "persons":
        years = span(doc.get("times", []) + doc.get("places", []))
        if years:
            parts.append(f"years: {years[0]}–{years[1]}")
    if collection == "works" and doc.get("authors"):
        parts.append(f"authors: {', '.join(snapshot_names.get(a, a) for a in doc['authors'])}")
    if collection == "places" and doc.get("location"):
        parts.append(f"coords: {doc['location']['coordinates']}")
    return " | ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Find existing DB records and already-extracted SEP entities by name.")
    parser.add_argument("collection", choices=COLLECTIONS)
    parser.add_argument("query", nargs="*")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--list", action="store_true", help="List every record of the collection")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--entries", type=Path, default=ENTRIES_DIR)
    args = parser.parse_args()

    snapshot = load_snapshot(args.snapshot)
    names = {d["_id"]: d["name"] for d in snapshot["persons"]}
    if args.list:
        for doc in sorted(snapshot[args.collection], key=lambda d: normalize(doc_label(args.collection, d) or "")):
            print(describe_db(args.collection, doc, names))
        return

    query = " ".join(args.query)
    if not query:
        raise SystemExit("query required unless --list")
    results = []
    for doc in snapshot[args.collection]:
        s = score(query, [doc_label(args.collection, doc) or ""] + doc_alt_labels(args.collection, doc))
        if s >= args.threshold:
            results.append((s, "db", describe_db(args.collection, doc, names)))
    if args.collection in EXTRACTION_KEYS:
        for entry, extraction in load_extractions(args.entries).items():
            for item in extraction.get(args.collection, []):
                labels = [item.get(EXTRACTION_KEYS[args.collection]) or ""] + item.get("alt_names", []) + item.get("alt_titles", [])
                s = score(query, labels)
                if s >= args.threshold:
                    extra = f" | db_id: {item['db_id']}" if item.get("db_id") else ""
                    results.append((s, "sep", f"sep:{entry}/{item['key']} | {labels[0]}{extra}"))
    results.sort(key=lambda r: -r[0])
    for s, origin, text in results[: args.limit]:
        print(f"{s:.2f} [{origin}] {text}")
    if not results:
        print("no matches")


if __name__ == "__main__":
    main()
