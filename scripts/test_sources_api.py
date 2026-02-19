import sys
import os
import requests

# Test local API (assuming server running, but I can also use internal test like before)
# Better to use internal test to avoid needing server running

sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
from app.core.config import settings

# Hardcode correct data dir for testing
DATA_DIR = "/Users/nogashlomi/projects/yossi/RDF_project_copy/data"
ONTOLOGY_DIR = "/Users/nogashlomi/projects/yossi/RDF_project_copy/data/ontology"

print(f"Loading data from {DATA_DIR}...")
rdf_store.load_data([DATA_DIR, ONTOLOGY_DIR])

print("Testing list_sources()...")
try:
    sources = entity_service.list_sources()
    print(f"Success! Got {len(sources)} sources.")
    for s in sources:
        print(f" - {s.label}: {s.count}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
