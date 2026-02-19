import sys
from app.core.rdf_store import rdf_store
from app.core.config import settings

# Load data
print("Loading data...")
rdf_store.load_data([settings.DATA_DIR, settings.ONTOLOGY_DIR])

q = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?uri ?authorUri ?authorName
WHERE {
    ?uri a jp:ScholarlyWork .
    # Authors (Scholars)
    OPTIONAL { 
        ?uri jp:hasAuthor ?authorUri .
        ?authorUri rdfs:label ?authorName .
    }
    FILTER (regex(str(?uri), "Science_Medieval"))
}
"""

print("Running query...")
for row in rdf_store.query(q):
    print(f"URI: {row.uri}")
    print(f"AuthorURI: {row.authorUri}")
    print(f"AuthorName: {row.authorName}")
    print("-" * 20)

