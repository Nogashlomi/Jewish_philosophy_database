from app.services.entity_service import entity_service
from app.core.rdf_store import rdf_store
rdf_store.load_data()
data = entity_service.get_network_data("Zonta")
print("Nodes:", len(data.nodes))
print("Edges:", len(data.edges))
