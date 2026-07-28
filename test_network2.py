import sys, os
sys.path.append(os.path.abspath('.'))
from backend.app.services.entity_service import entity_service

sources = entity_service.get_sources()
print('Sources:', sources)
net_all = entity_service.get_network_data()
print('All nodes:', len(net_all.nodes), 'edges:', len(net_all.edges))
if sources:
    source_id = sources[0]['id']
    net_src = entity_service.get_network_data(source=source_id)
    print('Filtered nodes:', len(net_src.nodes), 'edges:', len(net_src.edges))
