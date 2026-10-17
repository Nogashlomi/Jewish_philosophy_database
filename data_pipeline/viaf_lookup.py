import csv
import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

JP = Namespace("http://jewish_philosophy.org/ontology#")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_CSV = DATA_DIR / "viaf_lookup.csv"
SEARCH_URL = "https://viaf.org/viaf/AutoSuggest"
USER_AGENT = "JewishPhilosophyDatabase-VIAFLookup/1.0"
MAX_RESULTS = 3
REQUEST_DELAY = 1.0
MAX_NETWORK_RETRIES = 5
DEFAULT_RATE_LIMIT_WAIT = 60
FIELDNAMES = ["name"] + [f"{field}_{i}" for i in range(1, MAX_RESULTS + 1) for field in ("viaf_id", "viaf_name")]


class RateLimited(Exception):
    def __init__(self, wait_seconds):
        super().__init__(f"rate limited, wait {wait_seconds}s")
        self.wait_seconds = wait_seconds


def load_person_names():
    g = Graph()
    for ttl in sorted(DATA_DIR.rglob("*.ttl")):
        g.parse(ttl, format="turtle")
    names = set()
    for person in g.subjects(RDF.type, JP.HistoricalPerson):
        for label in g.objects(person, RDFS.label):
            names.add(str(label).strip())
    return sorted(n for n in names if n)


def load_done_names():
    if not OUTPUT_CSV.exists():
        return set()
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
        return {row["name"] for row in csv.DictReader(f)}


def header_seconds(headers, *names):
    for name in names:
        value = headers.get(name)
        if value is not None:
            try:
                return max(int(float(value)), 1)
            except ValueError:
                continue
    return None


def search(name):
    url = f"{SEARCH_URL}?" + urllib.parse.urlencode({"query": name}, quote_via=urllib.parse.quote)
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            headers = response.headers
    except urllib.error.HTTPError as e:
        if e.code == 429:
            wait = header_seconds(e.headers, "Retry-After", "RateLimit-Reset") or DEFAULT_RATE_LIMIT_WAIT
            raise RateLimited(wait)
        raise
    remaining = header_seconds(headers, "RateLimit-Remaining")
    if headers.get("RateLimit-Remaining") == "0":
        wait = header_seconds(headers, "RateLimit-Reset") or DEFAULT_RATE_LIMIT_WAIT
        logging.warning(f"Rate limit quota exhausted, sleeping {wait}s before next request")
        time.sleep(wait)
    elif remaining is not None and remaining % 100 == 0:
        logging.info(f"Rate limit remaining: {remaining}")
    return body


def parse_results(body):
    results = []
    seen = set()
    for item in body.get("result") or []:
        viaf_id = str(item.get("viafid") or "")
        if item.get("nametype") != "personal" or not viaf_id or viaf_id in seen:
            continue
        seen.add(viaf_id)
        results.append((viaf_id, item.get("displayForm") or item.get("term") or ""))
    return results[:MAX_RESULTS]


def strip_parentheses(name):
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", " ", name)).strip()


def search_with_retries(name):
    attempt = 0
    while True:
        try:
            return parse_results(search(name))
        except RateLimited as e:
            logging.warning(f"Rate limited on '{name}', sleeping {e.wait_seconds}s")
            time.sleep(e.wait_seconds)
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code < 500:
                raise
            attempt += 1
            if attempt > MAX_NETWORK_RETRIES:
                raise
            wait = 2 ** attempt
            logging.warning(f"Network error on '{name}' ({e}), retry {attempt}/{MAX_NETWORK_RETRIES} in {wait}s")
            time.sleep(wait)


def main():
    names = load_person_names()
    done = load_done_names()
    pending = [n for n in names if n not in done]
    logging.info(f"{len(names)} names, {len(done)} already in CSV, {len(pending)} to look up")

    new_file = not OUTPUT_CSV.exists() or os.path.getsize(OUTPUT_CSV) == 0
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if new_file:
            writer.writeheader()
            f.flush()
        for index, name in enumerate(pending, 1):
            try:
                results = search_with_retries(name)
                stripped = strip_parentheses(name)
                if not results and stripped and stripped != name:
                    time.sleep(REQUEST_DELAY)
                    results = search_with_retries(stripped)
            except Exception as e:
                logging.error(f"Failed '{name}': {e}")
                time.sleep(REQUEST_DELAY)
                continue
            row = {"name": name}
            for i, (viaf_id, viaf_name) in enumerate(results, 1):
                row[f"viaf_id_{i}"] = viaf_id
                row[f"viaf_name_{i}"] = viaf_name
            writer.writerow(row)
            f.flush()
            logging.info(f"[{index}/{len(pending)}] {name}: {len(results)} results")
            time.sleep(REQUEST_DELAY)


if __name__ == "__main__":
    main()
