import sys
import os
from rdflib import Graph, Namespace, URIRef, RDFS, RDF
from collections import defaultdict

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.core.config import settings
from app.core.rdf_store import rdf_store

print("Loading data...")
rdf_store.load_data([settings.DATA_DIR, settings.ONTOLOGY_DIR])

JP = Namespace("http://jewish_philosophy.org/ontology#")

print("Scanning for duplicate places...")

# Map label -> list of URIs
places_by_label = defaultdict(list)

for s, p, o in rdf_store.g.triples((None, RDF.type, JP.Place)):
    label = rdf_store.g.value(s, RDFS.label)
    if label:
        normalized_label = str(label).strip().lower()
        places_by_label[normalized_label].append({
            "uri": str(s),
            "original_label": str(label)
        })

duplicates = {k: v for k, v in places_by_label.items() if len(v) > 1}

print(f"Found {len(duplicates)} duplicate labels.")

for label, entries in duplicates.items():
    print(f"\nLabel: '{label}'")
    for entry in entries:
        print(f"  - {entry['uri']} ({entry['original_label']})")
