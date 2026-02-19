from app.core.rdf_store import rdf_store
from app.services.entity_service import entity_service
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_query():
    print("Loading data...")
    rdf_store.load_data()
    
    print("Running query...")
    q = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?source ?label (COUNT(?work) as ?workCount)
    WHERE {
        ?source a jp:Source .
        OPTIONAL { ?source rdfs:label ?label }
        OPTIONAL { ?work jp:hasSource ?source }
    }
    GROUP BY ?source ?label
    ORDER BY DESC(?workCount)
    """
    
    results = rdf_store.query(q)
    results = rdf_store.query(q)
    print(f"Found {len(results)} sources:")
    for row in results:
        print(f"Source: {row.source}, Type: {type(row.source)}")
        print(f"Label: {row.label}")
        print(f"Count: {row.workCount}")
        print("-" * 20)

    # Test Places with Coordinates
    print("\n--- Places with Coordinates ---")
    q_places = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    SELECT (COUNT(?place) as ?count)
    WHERE {
        ?place jp:coordinates ?coords .
    }
    """
    for row in rdf_store.query(q_places):
        print(f"Total places with coordinates: {row.count}")

if __name__ == "__main__":
    test_query()
