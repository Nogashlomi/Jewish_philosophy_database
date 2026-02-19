import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.rdf_store import rdf_store
from app.core.config import settings
from rdflib import Namespace

# Hardcode correct data dir
DATA_DIR = "/Users/nogashlomi/projects/yossi/RDF_project_copy/data"
ONTOLOGY_DIR = "/Users/nogashlomi/projects/yossi/RDF_project_copy/data/ontology"

print(f"Loading data from {DATA_DIR}...")
rdf_store.load_data([DATA_DIR, ONTOLOGY_DIR])

JP = Namespace("http://jewish_philosophy.org/ontology#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

q = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?source ?label (COUNT(?work) as ?count)
WHERE {
    ?source a jp:Source .
    OPTIONAL { ?source rdfs:label ?label }
    OPTIONAL { ?work jp:hasSource ?source }
}
GROUP BY ?source ?label
ORDER BY DESC(?count)
"""

print("\n--- Sources Analysis ---")
results = rdf_store.query(q)
for row in results:
    s_id = row.source.split("#")[-1]
    label = row.label or s_id
    count = row.count
    print(f"Source: {label} ({s_id}) - Count: {count}")
