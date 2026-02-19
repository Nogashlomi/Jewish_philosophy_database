from rdflib import Graph, Namespace
import sys

# Load the file
g = Graph()
g.parse("data/scholarly-work.ttl", format="turtle")

JP = Namespace("http://jewish_philosophy.org/ontology#")

# Identify H_ works
# They seem to have URIs like jp:H_...
to_remove = []
for s, p, o in g:
    if "H_" in str(s):
        to_remove.append((s, p, o))
        
print(f"Found {len(to_remove)} triples related to H_ works.")

# Remove them
for t in to_remove:
    g.remove(t)
    
print(f"Remaining triples: {len(g)}")

# Save back
g.serialize("data/scholarly-work.ttl", format="turtle")
print("Saved cleaned file.")
