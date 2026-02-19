import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.entity_service import EntityService
from app.core.rdf_store import rdf_store

def test_scholarly_list():
    print("Loading data...")
    rdf_store.load_data(["data"])
    
    print("Testing list_scholarly_works...")
    service = EntityService()
    try:
        results = service.list_scholarly_works()
        print(f"Success! Got {len(results)} works.")
        if results:
            print("Sample:", results[0])
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scholarly_list()
