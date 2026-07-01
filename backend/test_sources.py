from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
rdf_store.load_data()
sources = entity_service.get_sources()
print("Sources:", sources)
