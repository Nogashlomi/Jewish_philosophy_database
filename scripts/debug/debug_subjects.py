from app.core.rdf_store import rdf_store
from app.core import queries
import sys

# Load data
print("Loading data...")
rdf_store.load_data()

print("\n--- QUERYING LIST_SUBJECTS ---")
results = rdf_store.query(queries.LIST_SUBJECTS)
for row in results:
    print(f"Subject: {row.label}, URI: {row.uri}, Count: {row.count}")

print("\n--- DEBUGGING ASTRONOMY TRIPLES ---")
q = """
SELECT ?s ?p ?o
WHERE {
    ?s <http://jewish_philosophy.org/ontology#hasSubject> <http://jewish_philosophy.org/ontology#Subject_Astronomy> .
}
LIMIT 5
"""
print("Checking for triples with Subject_Astronomy as object:")
res = rdf_store.query(q)
for row in res:
    print(f"  {row.s} hasSubject Astronomy")

print(f"Total such triples: {len(res)}")
