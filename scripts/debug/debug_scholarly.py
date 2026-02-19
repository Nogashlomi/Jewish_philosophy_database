import sys
import asyncio
from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
from app.core.config import settings

# Load data manually since we are not running the app
print("Loading data...")
rdf_store.load_data([settings.DATA_DIR, settings.ONTOLOGY_DIR])

# ID from scholarly-gad.ttl
work_id = "SW_Gad_Science_Medieval"

print(f"Fetching detail for {work_id}...")
try:
    detail = entity_service.get_scholarly_detail(work_id)
    print("Success!")
    print(detail)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

