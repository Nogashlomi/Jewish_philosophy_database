from app.core.rdf_store import rdf_store
from app.services.entity_service import entity_service

rdf_store.load_data()
try:
    data = entity_service.get_network_data()
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
