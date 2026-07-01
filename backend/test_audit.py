from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
rdf_store.load_data()
audit = entity_service.get_ontology_audit()
import json
print(json.dumps(audit, indent=2))
