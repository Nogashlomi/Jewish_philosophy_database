import sys
import site
sys.path.append('backend')
sys.path.append(site.getusersitepackages())
from app.services.entity_service import entity_service

def test(source=None):
    net = entity_service.get_network_data(source)
    print(f'Source: {source or "None"} -> Nodes: {len(net.nodes)}, Edges: {len(net.edges)}')

if __name__ == '__main__':
    test()
    test('example_source')
