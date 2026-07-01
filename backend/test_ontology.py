from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
rdf_store.load_data()
g = entity_service.get_ontology_graph()
for e in g["edges"]:
    print(e)
