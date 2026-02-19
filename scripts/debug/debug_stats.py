import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path("/Users/nogashlomi/projects/yossi/RDF_project_copy/backend")
sys.path.append(str(backend_path))

from app.core.rdf_store import rdf_store
from app.core.config import settings
from app.services.entity_service import entity_service

print("Loading data...")
rdf_store.load_data([settings.DATA_DIR, settings.ONTOLOGY_DIR])

print("Testing get_global_stats...")
try:
    stats = entity_service.get_global_stats()
    print("Stats:", stats)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
