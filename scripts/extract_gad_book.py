import sys
import os
import re
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD
from pypdf import PdfReader
import urllib.request
import urllib.parse
import json
import time

# Setup
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.core.config import settings

DATA_DIR = Path("/Users/nogashlomi/projects/yossi/RDF_project_copy/data")
PDF_PATH = Path("/Users/nogashlomi/projects/yossi/Gad - Science in Medieval Jewish Cultures (Gad Freudenthal (ed.)) (z-lib.org).pdf")

JP = Namespace("http://jewish_philosophy.org/ontology#")
g = Graph()
g.bind("jp", JP)

# 1. Load Existing Data to avoiding duplicates
print("Loading existing data for reconciliation...")
existing_persons = {} # label -> uri
existing_works = {}   # title -> uri

if (DATA_DIR / "persons.ttl").exists():
    g_existing = Graph()
    g_existing.parse(DATA_DIR / "persons.ttl", format="turtle")
    for s, _, o in g_existing.triples((None, RDFS.label, None)):
        existing_persons[str(o).lower()] = s

print(f"Loaded {len(existing_persons)} existing persons.")

# 2. Define New Source & Scholarly Work
SOURCE_URI = JP.Source_Books_and_Indexes
g.add((SOURCE_URI, RDF.type, JP.Source))
g.add((SOURCE_URI, RDFS.label, Literal("Books and Indexes")))

BOOK_URI = JP.SW_Gad_Science_Medieval
g.add((BOOK_URI, RDF.type, JP.ScholarlyWork))
g.add((BOOK_URI, JP.title, Literal("Science in Medieval Jewish Cultures")))
g.add((BOOK_URI, JP.publicationYear, Literal("2011", datatype=XSD.gYear))) # Verified year
g.add((BOOK_URI, JP.hasAuthor, JP.Scholar_Gad_Freudenthal)) 
g.add((BOOK_URI, JP.hasSource, SOURCE_URI))
g.add((BOOK_URI, RDFS.label, Literal("Science in Medieval Jewish Cultures")))

# Update Popularization of Philosophy to use this source
POPULARIZATION_URI = JP.Source_Popularization
g.add((POPULARIZATION_URI, RDF.type, JP.ScholarlyWork))
g.add((POPULARIZATION_URI, JP.hasSource, SOURCE_URI))
# Ensure title/label are preserved (they are already in other files, but adding them here in new file is fine or just the link)
# Adding type and source is enough to make it appear as a Work under this Source.

# 3. Extraction Logic
print(f"Reading PDF: {PDF_PATH}...")
reader = PdfReader(PDF_PATH)
text_content = ""
pages_to_scan = list(range(10, 50)) + list(range(len(reader.pages)-30, len(reader.pages)))

extracted_names = set()

for i in pages_to_scan:
    try:
        page = reader.pages[i]
        text = page.extract_text()
        found = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+)', text)
        for name in found:
            if name.lower() not in ["The University", "New York", "Middle Ages", "Jewish Philosophy", "Gad Freudenthal"]: 
                extracted_names.add(name)
    except:
        pass

print(f"Potential names found: {len(extracted_names)}")

# 4. Enrichment (Wikidata)
def fetch_wikidata(name):
    base_url = "https://www.wikidata.org/w/api.php"
    params = urllib.parse.urlencode({
        "action": "wbsearchentities",
        "search": name,
        "language": "en",
        "format": "json"
    })
    url = f"{base_url}?{params}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get("search"):
                # Return first result
                return data["search"][0]
    except Exception as e:
        print(f"Error fetching {name}: {e}")
    return None

new_triples_count = 0

print("Enriching and linking...")
for name in list(extracted_names)[:20]: 
    if name.lower() in existing_persons:
        # Link
        person_uri = existing_persons[name.lower()]
        g.add((BOOK_URI, JP.mentionsPerson, person_uri))
        print(f"Linked existing: {name}")
    else:
        # Fetch details
        print(f"Fetching Wikidata for: {name}")
        wd_data = fetch_wikidata(name)
        if wd_data:
            wd_id = wd_data.get("id")
            description = wd_data.get("description", "")
            
            if "human" in description or "philosopher" in description or "rabbi" in description or "writer" in description:
                new_uri = JP[f"Q_{wd_id}"]
                g.add((new_uri, RDF.type, JP.HistoricalPerson))
                g.add((new_uri, RDFS.label, Literal(wd_data["label"])))
                g.add((new_uri, JP.description, Literal(description)))
                
                # Link book to new person
                g.add((BOOK_URI, JP.mentionsPerson, new_uri))
                new_triples_count += 1
                print(f"Created new: {name} ({wd_id})")
        
        time.sleep(0.5)

# 5. Save
output_file = DATA_DIR / "scholarly-gad.ttl"
g.serialize(output_file, format="turtle")
print(f"Saved {len(g)} triples to {output_file}")
