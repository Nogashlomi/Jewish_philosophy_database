from app.core.rdf_store import rdf_store
from rdflib import Namespace, RDF

JP = Namespace("http://jewish_philosophy.org/ontology#")

def debug():
    print("Loading data...")
    rdf_store.load_data()
    
    print("\n--- ALL jp:Source Instances ---")
    q = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    SELECT ?s ?label WHERE {
        ?s a jp:Source .
        OPTIONAL { ?s rdfs:label ?label }
    }
    """
    for row in rdf_store.query(q):
        print(f"Source: {row.s} (Label: {row.label})")
        
    print("\n--- SAMPLE jp:hasSource Values ---")
    q2 = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    SELECT ?p ?source WHERE {
        ?p a jp:HistoricalPerson .
        ?p jp:hasSource ?source .
    } LIMIT 10
    """
    for row in rdf_store.query(q2):
        print(f"Person: {row.p} -> Source: {row.source} (Type: {type(row.source)})")

if __name__ == "__main__":
    debug()
