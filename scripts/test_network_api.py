import sys
import os
import traceback

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
from app.core.config import settings

# Hardcode correct data dir for testing
DATA_DIR = "/Users/nogashlomi/projects/yossi/RDF_project_copy/data"
ONTOLOGY_DIR = "/Users/nogashlomi/projects/yossi/RDF_project_copy/data/ontology"

print(f"Loading data from {DATA_DIR}...")
rdf_store.load_data([DATA_DIR, ONTOLOGY_DIR])

print("Testing get_network_data()...")
try:
    data = entity_service.get_network_data()
    print(f"Success! Got {len(data.nodes)} nodes and {len(data.edges)} edges.")
    print(f"Success! Got {len(data.nodes)} nodes and {len(data.edges)} edges.")
    
    # Check for ScholarlyWork nodes specifically
    sw_nodes = [n for n in data.nodes if n.group == 'ScholarlyWork']
    if sw_nodes:
        print(f"Found {len(sw_nodes)} ScholarlyWork nodes.")
        print("Sample ScholarlyWork node:", sw_nodes[0])
    else:
        print("No ScholarlyWork nodes found!")
except Exception as e:
    print(f"Error in network: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting list_subjects()...")
try:
    subjects = entity_service.list_subjects()
    print(f"Success! Got {len(subjects)} subjects.")
    if subjects:
        print("Sample subject:", subjects[0])
except Exception as e:
    print(f"Error in subjects: {e}")
    traceback.print_exc()
