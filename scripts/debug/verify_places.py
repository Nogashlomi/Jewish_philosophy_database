import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.entity_service import entity_service

try:
    print("Testing list_places()...")
    places = entity_service.list_places()
    print(f"Found {len(places)} places.")
    if len(places) > 0:
        print(f"First place: {places[0]}")
    else:
        print("No places found (this might be expected if DB is empty, but checking for errors).")

    print("\nTesting get_place_detail()...")
    # Try to get detail for the first place if exists
    if len(places) > 0:
        p_id = places[0].id
        detail = entity_service.get_place_detail(p_id)
        print(f"Detail for {p_id}: {detail}")
    
    print("\nService Verification Successful.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
