from app.core.rdf_store import rdf_store
from app.core.config import settings
import sys

# Mock settings just in case
print(f"Loading data from: {settings.DATA_DIR} and {settings.ONTOLOGY_DIR}")

try:
    rdf_store.load_data([settings.DATA_DIR, settings.ONTOLOGY_DIR])
    print("SUCCESS: Graph loaded.")
    print(f"Total Triples: {len(rdf_store.g)}")
    
    # Simple query to list a few classes
    q = """
    SELECT DISTINCT ?type WHERE {
        ?s a ?type .
    } LIMIT 5
    """
    print("Types found:")
    for row in rdf_store.query(q):
        print(f" - {row.type}")

except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
