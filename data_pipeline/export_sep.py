import argparse
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "https://plato.stanford.edu"
CONTENTS_URL = f"{BASE_URL}/contents.html"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sep"
CRAWL_DELAY = 5
TIMEOUT = 60
RETRIES = 4
ENTRY_LINK = re.compile(r"^entries/([^/#]+)/?$")
LOCAL_PAGE = re.compile(r"^([^/#?:]+\.html)(?:#.*)?$")


class Fetcher:
    def __init__(self, delay: float):
        self.delay = delay
        self.last = 0.0
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "jephy-sep-export (research; respects crawl-delay)"

    def get(self, url: str) -> requests.Response:
        for attempt in range(1, RETRIES + 1):
            wait = self.last + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            try:
                response = self.session.get(url, timeout=TIMEOUT)
                if response.status_code == 404:
                    return response
                response.raise_for_status()
                response.encoding = "utf-8"
                return response
            except requests.RequestException as e:
                if attempt == RETRIES:
                    raise
                backoff = 15 * attempt
                logging.warning(f"{url} failed ({e}), retry {attempt}/{RETRIES - 1} in {backoff}s")
                time.sleep(backoff)


def absolutize(element, page_url: str):
    for tag in element.find_all(href=True):
        tag["href"] = urljoin(page_url, tag["href"])
    for tag in element.find_all(src=True):
        tag["src"] = urljoin(page_url, tag["src"])
    return element


def to_markdown(element, page_url: str) -> str:
    if element is None:
        return ""
    html = str(absolutize(element, page_url))
    text = markdownify(html, heading_style="ATX", escape_underscores=False, escape_asterisks=False)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def without_heading(element):
    if element is not None:
        heading = element.find(re.compile(r"^h[1-6]$"))
        if heading:
            heading.decompose()
    return element


def meta(soup, name: str) -> list[str]:
    tags = soup.find_all("meta", attrs={"name": name}) + soup.find_all("meta", attrs={"property": name})
    return [t["content"].strip() for t in tags if t.get("content")]


def first(values: list[str]) -> str | None:
    return values[0] if values else None


def parse_toc(toc) -> list[dict]:
    if toc is None:
        return []
    items = []
    for link in toc.find_all("a", href=True):
        level = len(link.find_parents("ul"))
        items.append({"anchor": link["href"].lstrip("#"), "title": link.get_text(" ", strip=True), "level": level})
    return items


def parse_related(related) -> list[dict]:
    if related is None:
        return []
    entries = []
    for link in related.find_all("a", href=True):
        identifier = link["href"].strip("./").split("/")[0]
        entries.append({"identifier": identifier, "title": link.get_text(" ", strip=True)})
    return entries


def local_pages(soup) -> list[str]:
    pages = []
    for link in soup.select("#main-text a[href], #bibliography a[href], #preamble a[href]"):
        match = LOCAL_PAGE.match(link["href"])
        if match and match.group(1) not in pages:
            pages.append(match.group(1))
    return pages


def parse_page_body(html: str, page_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find(id="aueditable") or soup.find(id="article-content") or soup.find(id="content")
    title = content.find("h1") if content else None
    title_text = title.get_text(" ", strip=True) if title else None
    if title:
        title.decompose()
    return {"title": title_text, "markdown": to_markdown(content, page_url)}


def parse_entry(identifier: str, url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    pubinfo = soup.find(id="pubinfo")
    h1 = soup.select_one("#aueditable h1") or soup.find("h1")
    return {
        "identifier": identifier,
        "url": url,
        "title": first(meta(soup, "citation_title")) or (h1.get_text(" ", strip=True) if h1 else None),
        "authors": meta(soup, "citation_author") or meta(soup, "DC.creator"),
        "first_published": first(meta(soup, "DCTERMS.issued")),
        "last_modified": first(meta(soup, "DCTERMS.modified")),
        "pubinfo": pubinfo.get_text(" ", strip=True) if pubinfo else None,
        "preamble": to_markdown(soup.find(id="preamble"), url),
        "toc": parse_toc(soup.find(id="toc")),
        "main_text": to_markdown(soup.find(id="main-text"), url),
        "bibliography": to_markdown(without_heading(soup.find(id="bibliography")), url),
        "other_internet_resources": to_markdown(without_heading(soup.find(id="other-internet-resources")), url),
        "related_entries": parse_related(soup.find(id="related-entries")),
        "copyright": to_markdown(soup.find(id="article-copyright"), url),
        "notes": "",
        "supplements": [],
    }


def entry_markdown(entry: dict) -> str:
    lines = [f"# {entry['title']}", ""]
    lines.append(f"- **Identifier:** {entry['identifier']}")
    lines.append(f"- **URL:** {entry['url']}")
    lines.append(f"- **Authors:** {'; '.join(entry['authors'])}")
    lines.append(f"- **First published:** {entry['first_published']}")
    lines.append(f"- **Last modified:** {entry['last_modified']}")
    lines.append("")
    for heading, key in [("Preamble", "preamble"), (None, "main_text"), ("Bibliography", "bibliography"), ("Notes", "notes"), ("Other Internet Resources", "other_internet_resources")]:
        if entry[key]:
            if heading:
                lines += [f"## {heading}", ""]
            lines += [entry[key], ""]
    if entry["related_entries"]:
        lines += ["## Related Entries", ""]
        lines += [f"- [{r['title']}]({BASE_URL}/entries/{r['identifier']}/)" for r in entry["related_entries"]]
        lines.append("")
    for supplement in entry["supplements"]:
        lines += [f"## Supplement: {supplement['title'] or supplement['file']}", "", supplement["markdown"], ""]
    if entry["copyright"]:
        lines += ["---", "", entry["copyright"], ""]
    return "\n".join(lines)


def list_entries(fetcher: Fetcher) -> list[str]:
    soup = BeautifulSoup(fetcher.get(CONTENTS_URL).text, "html.parser")
    content = soup.find(id="content") or soup
    identifiers = []
    for link in content.find_all("a", href=True):
        match = ENTRY_LINK.match(link["href"].strip())
        if match and match.group(1) not in identifiers:
            identifiers.append(match.group(1))
    return identifiers


def export_entry(fetcher: Fetcher, identifier: str, dirs: dict) -> dict | None:
    url = f"{BASE_URL}/entries/{identifier}/"
    response = fetcher.get(url)
    if response.status_code == 404:
        logging.warning(f"{identifier}: 404")
        return None
    final_url = response.url
    if urlparse(final_url).path.rstrip("/") != urlparse(url).path.rstrip("/"):
        logging.info(f"{identifier}: redirected to {final_url}")
    entry_html_dir = dirs["html"] / identifier
    entry_html_dir.mkdir(parents=True, exist_ok=True)
    (entry_html_dir / "index.html").write_text(response.text, encoding="utf-8")

    entry = parse_entry(identifier, final_url, response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    for page in local_pages(soup):
        page_url = urljoin(final_url, page)
        page_response = fetcher.get(page_url)
        if page_response.status_code == 404:
            logging.warning(f"{identifier}: {page} 404")
            continue
        (entry_html_dir / page).write_text(page_response.text, encoding="utf-8")
        body = parse_page_body(page_response.text, page_url)
        if page == "notes.html":
            entry["notes"] = body["markdown"]
        else:
            entry["supplements"].append({"file": page, "url": page_url, "title": body["title"], "markdown": body["markdown"]})

    with open(dirs["json"] / f"{identifier}.json", "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    (dirs["md"] / f"{identifier}.md").write_text(entry_markdown(entry), encoding="utf-8")
    return entry


def write_combined(dirs: dict, output_dir: Path):
    paths = sorted(dirs["json"].glob("*.json"))
    with open(output_dir / "sep_entries.jsonl", "w", encoding="utf-8") as out:
        for path in paths:
            with open(path, encoding="utf-8") as f:
                out.write(json.dumps(json.load(f), ensure_ascii=False) + "\n")
    logging.info(f"wrote {len(paths)} entries to {output_dir / 'sep_entries.jsonl'}")


def main():
    parser = argparse.ArgumentParser(description="Export all Stanford Encyclopedia of Philosophy entries (JSON + Markdown + raw HTML).")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--entries", nargs="+", help="Export only these entry identifiers (e.g. maimonides spinoza)")
    parser.add_argument("--limit", type=int, help="Export only the first N entries from the table of contents")
    parser.add_argument("--force", action="store_true", help="Re-fetch entries that were already exported")
    parser.add_argument("--delay", type=float, default=CRAWL_DELAY, help="Seconds between requests (robots.txt crawl-delay is 5)")
    args = parser.parse_args()

    dirs = {name: args.output_dir / name for name in ("json", "md", "html")}
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    fetcher = Fetcher(args.delay)
    identifiers = args.entries or list_entries(fetcher)
    if args.limit:
        identifiers = identifiers[: args.limit]
    logging.info(f"{len(identifiers)} entries to process")

    failed = []
    for i, identifier in enumerate(identifiers, 1):
        if not args.force and (dirs["json"] / f"{identifier}.json").exists():
            continue
        try:
            entry = export_entry(fetcher, identifier, dirs)
            if entry is None:
                failed.append(identifier)
            else:
                logging.info(f"[{i}/{len(identifiers)}] {identifier}: {len(entry['supplements'])} supplements, notes={'yes' if entry['notes'] else 'no'}")
        except Exception as e:
            logging.error(f"[{i}/{len(identifiers)}] {identifier}: {e}")
            failed.append(identifier)

    write_combined(dirs, args.output_dir)
    if failed:
        logging.warning(f"{len(failed)} failed: {' '.join(failed)}")


if __name__ == "__main__":
    main()
