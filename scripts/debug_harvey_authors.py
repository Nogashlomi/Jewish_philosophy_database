import sys
import os
from rdflib import Graph, Namespace, URIRef, RDFS

# Setup paths
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.core.config import settings
from app.core.rdf_store import rdf_store

# Helper to simulate app loading
print("Loading data...")
settings.DATA_DIR = os.path.join(os.getcwd(), "data")
settings.ONTOLOGY_DIR = os.path.join(os.getcwd(), "data/ontology")
rdf_store.load_data([settings.DATA_DIR, settings.ONTOLOGY_DIR])

JP = Namespace("http://jewish_philosophy.org/ontology#")

# Target a known Harvey work from the previous view_file output
target_work = URIRef("http://jewish_philosophy.org/ontology#SW_New_0_Judah_ha_Levi__Abraham_Bar_Hiy")

print(f"\n--- Debugging Work: {target_work} ---")

# Check existence
if (target_work, None, None) not in rdf_store.g:
    print("Work NOT found in graph!")
else:
    print("Work found in graph.")

# Check Authors
print("\nAuthors linked:")
authors = list(rdf_store.g.objects(target_work, JP.hasAuthor))
if not authors:
    print("No authors found via jp:hasAuthor")
else:
    for author_uri in authors:
        print(f"  Author URI: {author_uri}")
        # Check Label
        label = rdf_store.g.value(author_uri, RDFS.label)
        print(f"    Label: {label}")
        # Check Type
        type_ = rdf_store.g.value(author_uri, RDFS.type) # Should be rdf:type? No, it's a property.
        # rdf:type is a predicate.
        types = list(rdf_store.g.objects(author_uri, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")))
        print(f"    Types: {types}")

# Run the SPARQL query from the service to see if it matches
print("\n--- Running Service SPARQL Query ---")
q = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?uri ?title ?authorUri ?authorName
WHERE {
    BIND(<http://jewish_philosophy.org/ontology#SW_New_0_Judah_ha_Levi__Abraham_Bar_Hiy> AS ?uri)
    ?uri a jp:ScholarlyWork .
    OPTIONAL { ?uri jp:title ?title }
    
    OPTIONAL { 
        ?uri jp:hasAuthor ?authorUri .
        ?authorUri rdfs:label ?authorName .
    }
}
"""
for row in rdf_store.query(q):
    print(f"Result: {row.title} | Author: {row.authorName} ({row.authorUri})")
