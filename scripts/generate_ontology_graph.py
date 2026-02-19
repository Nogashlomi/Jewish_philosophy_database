from pyvis.network import Network
from rdflib import Graph, RDF, RDFS, OWL, BNode, URIRef
import os

# Ensure output directory exists
output_dir = "frontend/public"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load your ontology
g = Graph()
ontology_path = "data/ontology/vocabulary.ttl"
print(f"Loading ontology from {ontology_path}...")
g.parse(ontology_path, format="turtle")

# Initialize Pyvis network
net = Network(height="800px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")

# Looser physics for more space and better dragging
net.barnes_hut(
    gravity=-8000,
    central_gravity=0.05,
    spring_length=350,
    spring_strength=0.03,
    damping=0.5,
    overlap=1.0
)
net.toggle_physics(True)

# Utility to create readable labels
def label(uri):
    if isinstance(uri, BNode):
        return str(uri)
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

# Handle unionOf for domains/ranges
def extract_classes(node):
    classes = []
    if node is None:
        return []
    if isinstance(node, BNode):
        union = g.value(node, OWL.unionOf)
        if union:
            for item in g.items(union):
                classes.append(item)
    elif isinstance(node, URIRef):
        classes.append(node)
    return classes

# Track nodes already added
added_nodes = set()
def add_node_safe(uri, shape="box", color="lightblue"):
    uri_str = str(uri)
    if uri_str not in added_nodes:
        net.add_node(uri_str, label=label(uri), shape=shape, color=color)
        added_nodes.add(uri_str)

# Collect all class nodes
all_classes = set(g.subjects(RDF.type, RDFS.Class)) | set(g.subjects(RDF.type, OWL.Class))
# Include domains/ranges from object properties only
for p in g.subjects(RDF.type, OWL.ObjectProperty):
    all_classes.update(extract_classes(g.value(p, RDFS.domain)))
    all_classes.update(extract_classes(g.value(p, RDFS.range)))

# Add all class nodes
for c in all_classes:
    add_node_safe(c, shape="box", color="#97C2FC") # Standard blue for classes

# Add object-property edges only (ignore datatype properties)
edge_count = 0
for p in g.subjects(RDF.type, OWL.ObjectProperty):
    domains = extract_classes(g.value(p, RDFS.domain))
    ranges = extract_classes(g.value(p, RDFS.range))
    for d in domains:
        for r in ranges:
            add_node_safe(d, shape="box", color="#97C2FC")
            add_node_safe(r, shape="box", color="#97C2FC")
            net.add_edge(str(d), str(r), label=label(p), arrows="to", color="gray")
            edge_count += 1

output_path = os.path.join(output_dir, "conceptual_graph.html")
# Save interactive HTML
net.write_html(output_path)
print(f"Graph saved as {output_path} with {len(all_classes)} nodes and {edge_count} edges.")
