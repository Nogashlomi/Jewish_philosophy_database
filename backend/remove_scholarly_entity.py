import re

with open('app/services/entity_service.py', 'r') as f:
    content = f.read()

# Remove list_scholarly_works and get_scholarly_detail completely
pattern = r'    def list_scholarly_works\(self,.*?\n(?:(?: {8,}.*?\n|^\s*\n)*).*?    def get_scholarly_detail\(self,.*?\n(?:(?: {8,}.*?\n|^\s*\n)*)'
content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Fix dangling sf_nodes in get_network_data
content = re.sub(r'\s*sf_nodes = self\._get_source_filter\(source, "s"\)\n', '\n', content)
content = re.sub(r'q_nodes = queries\.GET_NETWORK_NODES\.format\(_nodes, search_filter=""\)', 'q_nodes = queries.GET_NETWORK_NODES.format(search_filter="")', content)
content = re.sub(r'q_nodes = queries\.GET_NETWORK_NODES\.format\(\_nodes,\s*search_filter=""\)', 'q_nodes = queries.GET_NETWORK_NODES.format(search_filter="")', content)

# Check if we failed to remove the source filter from get_network_data in the first regex
content = re.sub(r'self\._get_source_filter\(source, "s"\)', '""', content)

with open('app/services/entity_service.py', 'w') as f:
    f.write(content)
