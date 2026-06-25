import re
with open('backend/app/services/entity_service.py', 'r') as f:
    c = f.read()

c = re.sub(r'def get_global_stats\(self, \) -> Dict\[str, int\]:', 'def get_global_stats(self, source: str = None) -> Dict[str, int]:', c)

with open('backend/app/services/entity_service.py', 'w') as f:
    f.write(c)
