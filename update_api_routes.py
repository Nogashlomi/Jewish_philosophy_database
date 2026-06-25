import re

# Update persons.py
with open('backend/app/api/persons.py', 'r') as f:
    c = f.read()
c = re.sub(r'def list_persons\(\n\s*page: int = Query\(1, ge=1, description="Page number"\),\n\s*page_size: int = Query\(100, ge=1, le=1000, description="Items per page"\)\n\):', 'def list_persons(\n    page: int = Query(1, ge=1, description="Page number"),\n    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),\n    source: Optional[str] = Query(None, description="Filter by data source ID")\n):', c)
c = re.sub(r'return entity_service\.list_persons\(page, page_size\)', 'return entity_service.list_persons(page, page_size, source)', c)
if 'Optional' not in c:
    c = c.replace('from typing import List', 'from typing import List, Optional')
with open('backend/app/api/persons.py', 'w') as f:
    f.write(c)

# Update index.py (for stats)
with open('backend/app/api/index.py', 'r') as f:
    c = f.read()
c = re.sub(r'def get_stats\(\):', 'def get_stats(source: Optional[str] = Query(None, description="Filter by data source ID")):', c)
c = re.sub(r'return entity_service\.get_global_stats\(\)', 'return entity_service.get_global_stats(source)', c)
if 'Optional' not in c:
    c = c.replace('from typing import Dict', 'from typing import Dict, Optional')
if 'Query' not in c:
    c = c.replace('from fastapi import APIRouter', 'from fastapi import APIRouter, Query')
with open('backend/app/api/index.py', 'w') as f:
    f.write(c)

# Update network.py
with open('backend/app/api/network.py', 'r') as f:
    c = f.read()
c = re.sub(r'def get_network\(\):', 'def get_network(source: Optional[str] = Query(None, description="Filter by data source ID")):', c)
c = re.sub(r'return entity_service\.get_network_data\(\)', 'return entity_service.get_network_data(source)', c)
if 'Optional' not in c:
    c = c.replace('from app.schemas.network import NetworkData', 'from app.schemas.network import NetworkData\nfrom typing import Optional\nfrom fastapi import Query')
with open('backend/app/api/network.py', 'w') as f:
    f.write(c)

