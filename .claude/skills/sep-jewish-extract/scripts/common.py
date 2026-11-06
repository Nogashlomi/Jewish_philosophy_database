import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WORK_DIR = REPO / "data" / "sep_import"
SNAPSHOT = REPO / "data" / "db_snapshot.json"
ENTRIES_DIR = WORK_DIR / "entries"
IDS_FILE = REPO / "data" / "sep_ids.json"
DEFAULT_EXPORT = Path("/home/liri/Stanford_Encyclopedia_of_Philosophy__Dump/export")
APOSTROPHES = re.compile(r"[’‘'`ʿʾʼ´]")
PUNCTUATION = re.compile(r"[^\w\s]")
BRACKETED = re.compile(r"\[([^\]]+)\]|\(([^)]+)\)")
SPAN_TOLERANCE = 40
UNNAMED = {"anonymous", "anon", "unknown", "pseudo"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = APOSTROPHES.sub("", text.lower())
    text = PUNCTUATION.sub(" ", text.replace("_", " "))
    return " ".join(text.split())


def variants(*names: str) -> set:
    found = set()
    for name in names:
        if not name:
            continue
        pseudo = False
        for match in BRACKETED.finditer(name):
            inner = (match.group(1) or match.group(2)).strip()
            if normalize(inner).startswith("pseudo"):
                pseudo = True
                continue
            if re.search(r"[\d?]", inner) or not inner[:1].isupper() or normalize(inner) in UNNAMED or len(normalize(inner)) < 4:
                continue
            found.add(normalize(inner))
        base = BRACKETED.sub("", name)
        if normalize(base).split(" ")[0] in UNNAMED:
            continue
        found.add(("pseudo " if pseudo else "") + normalize(base))
        if base.count(",") == 1:
            last, first = base.split(",")
            found.add(("pseudo " if pseudo else "") + normalize(f"{first} {last}"))
    return {v for v in found if v}


def similarity(a: str, b: str) -> float:
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    jaccard = len(ta & tb) / len(ta | tb)
    return max(ratio, jaccard)


def similar_normalized(a: str, b: str, threshold: float) -> bool:
    if not a or not b:
        return False
    ta, tb = set(a.split()), set(b.split())
    if len(ta & tb) / len(ta | tb) >= threshold:
        return True
    matcher = SequenceMatcher(None, a, b)
    return matcher.real_quick_ratio() >= threshold and matcher.quick_ratio() >= threshold and matcher.ratio() >= threshold


def span(times: list) -> tuple | None:
    starts = [t["from"] for t in times if isinstance(t.get("from"), int)]
    ends = [t.get("until", t.get("from")) for t in times if isinstance(t.get("from"), int)]
    return (min(starts), max(ends)) if starts else None


def spans_compatible(a: tuple | None, b: tuple | None) -> bool:
    if a is None or b is None:
        return True
    return a[0] - SPAN_TOLERANCE <= b[1] and b[0] - SPAN_TOLERANCE <= a[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_snapshot(path: Path = SNAPSHOT) -> dict:
    if not path.exists():
        raise SystemExit(f"missing DB snapshot {path}; run the db-snapshot skill")
    return load_json(path)


def load_extractions(directory: Path = ENTRIES_DIR) -> dict:
    return {path.stem: load_json(path) for path in sorted(directory.glob("*.json"))} if directory.exists() else {}


def doc_label(collection: str, doc: dict) -> str:
    return doc.get("title") if collection == "works" else doc.get("name")


def doc_alt_labels(collection: str, doc: dict) -> list:
    return doc.get("alt_titles", []) if collection == "works" else doc.get("alt_names", [])
