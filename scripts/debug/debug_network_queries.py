
from app.core.rdf_store import rdf_store, JP, RDF, RDFS
import sys
import glob

# Ensure data is loaded
def load_data():
    print("Loading data...")
    for file in glob.glob("data/*.ttl"):
        try:
            rdf_store.g.parse(file, format="turtle")
            print(f"Loaded {file}")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    print(f"Total triples: {len(rdf_store.g)}")

# Mock mk_id from router
def mk_id(uri): 
    return uri.split("/")[-1].split("#")[-1] # Robust split

def debug_network():
    load_data()
    print("--- Debugging Network Data ---")
    
    # 1. Query Nodes
    q_nodes = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?s ?label ?type
    WHERE {
        ?s a ?type .
        OPTIONAL { ?s rdfs:label ?label }
        FILTER (?type IN (jp:HistoricalPerson, jp:HistoricalWork, jp:ScholarlyWork, jp:Place, jp:Subject, jp:HistoricalLanguage))
    }
    """
    
    print("Querying Nodes...")
    results = list(rdf_store.query(q_nodes))
    print(f"Found {len(results)} nodes.")
    
    node_map = {}
    for row in results:
        nid = mk_id(row.s)
        node_map[row.s] = nid
    
    # 2. Query Edges
    q_direct = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    SELECT ?s ?p ?o
    WHERE {
        ?s ?p ?o .
        FILTER (?p IN (
            jp:writtenBy, 
            jp:aboutPerson, 
            jp:aboutWork, 
            jp:hasSubject, 
            jp:writtenInLanguage
        ))
    }
    """
    
    print("Querying Direct Edges...")
    edges = list(rdf_store.query(q_direct))
    print(f"Found {len(edges)} raw edges.")
    
    valid_edges = 0
    for row in edges:
        if row.s in node_map and row.o in node_map:
            valid_edges += 1
        else:
            # Print a few invalid ones to see why
            if valid_edges < 5:
                s_in = row.s in node_map
                o_in = row.o in node_map
                print(f"Missing Node for Edge: {mk_id(row.s)} -> {mk_id(row.o)} | S_in: {s_in}, O_in: {o_in}")
                if not s_in: print(f"  Missing Subject: {row.s}")
                if not o_in: print(f"  Missing Object: {row.o}")

    print(f"Valid Edges (both nodes exist): {valid_edges}")

    # Check specific example
    print("\n--- Checking specific example: Maimonides ---")
    maimonides_uri = None
    for s, nid in node_map.items():
        if "Maimonides" in nid or "Maimonides" in str(s):
            maimonides_uri = s
            print(f"Found Maimonides: {s}")
            break
            
    if maimonides_uri:
        # Check edges for Maimonides
        for row in edges:
            if row.o == maimonides_uri:
                print(f"  Incoming: {mk_id(row.s)} --[{mk_id(row.p)}]--> Maimonides")
            if row.s == maimonides_uri:
                print(f"  Outgoing: Maimonides --[{mk_id(row.p)}]--> {mk_id(row.o)}")

if __name__ == "__main__":
    debug_network()
