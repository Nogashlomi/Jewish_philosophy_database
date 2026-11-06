import argparse
import json
import re
from pathlib import Path

DEFAULT_EXPORT = Path("/home/liri/Stanford_Encyclopedia_of_Philosophy__Dump/export")
DEFAULT_OUT = Path(__file__).resolve().parents[4] / "data" / "sep_import" / "candidates.json"
JEWISH_TERMS = re.compile(
    r"\b(Jew(s|ess|ish|ry)?|Judaism|Judaic|Hebrew|rabbi(s|nic|nical)?|Talmud\w*|Torah|Kabbal\w*|Qabbal\w*|"
    r"Halakh\w*|Midrash\w*|Mishna\w*|synagogue|Zionis\w*|Hasid\w*|Karaite\w*|Sephardi\w*|Ashkenaz\w*|"
    r"converso\w*|Marrano\w*|Yiddish|Holocaust|Shoah)\b",
    re.IGNORECASE,
)
ANCESTRY = re.compile(
    r"\b(Jewish (family|parents|descent|origin|ancestry|background|community|heritage|by birth|mother|father)|"
    r"born (in|into) a\b[^.]{0,40}\bJewish|of Jewish\b|(a|as a) Jew\b|German-Jewish|Portuguese-Jewish|"
    r"converted (from|to) (Judaism|Christianity)|converso|Marrano|rabbi\b|yeshiva)",
    re.IGNORECASE,
)
LIFESPAN = re.compile(r"\(\s*(c\.\s*|ca\.\s*|b\.\s*|d\.\s*)?\d{1,4}(\s*(BCE|CE|BC|AD))?\s*[–—-]")
BIO_SECTION = re.compile(r"\b(Life|Biograph\w*|Early Years|Career)\b", re.IGNORECASE)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n\s*\n")


def is_biography(entry: dict) -> bool:
    if LIFESPAN.search(entry["preamble"][:600]):
        return True
    return any(BIO_SECTION.search(item["title"]) for item in entry["toc"] if item["level"] == 1)


def evidence(text: str, limit: int) -> list[str]:
    found = []
    for raw in SENTENCE_END.split(text):
        sentence = " ".join(raw.split())
        if sentence and ANCESTRY.search(sentence) and sentence not in found:
            found.append(sentence[:400])
        if len(found) >= limit:
            break
    return found


def classify(entry: dict) -> dict:
    body = entry["preamble"] + "\n" + entry["main_text"]
    hits = len(JEWISH_TERMS.findall(body))
    density = hits * 10000 / max(1, len(body))
    biography = is_biography(entry)
    ancestry = evidence(body, 6)
    if biography and (density >= 4 or ancestry):
        tier = "biography"
    elif not biography and density >= 1.5:
        tier = "topical"
    elif hits:
        tier = "mentions"
    else:
        tier = None
    return {
        "identifier": entry["identifier"],
        "title": entry["title"],
        "url": entry["url"],
        "tier": tier,
        "biography": biography,
        "jewish_term_hits": hits,
        "density": round(density, 2),
        "ancestry_evidence": ancestry,
        "related_entries": [r["identifier"] for r in entry["related_entries"]],
    }


def main():
    parser = argparse.ArgumentParser(description="Rank SEP entries by relevance to Jewish persons.")
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-hits", type=int, default=1)
    args = parser.parse_args()

    rows = []
    for path in sorted((args.export / "json").glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        row = classify(entry)
        if row["tier"] and row["jewish_term_hits"] >= args.min_hits:
            rows.append(row)
    order = {"biography": 0, "topical": 1, "mentions": 2}
    rows.sort(key=lambda r: (order[r["tier"]], -bool(r["ancestry_evidence"]), -r["density"]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for tier in order:
        print(f"{tier}: {sum(1 for r in rows if r['tier'] == tier)}")
    print(f"written {args.out}")


if __name__ == "__main__":
    main()
