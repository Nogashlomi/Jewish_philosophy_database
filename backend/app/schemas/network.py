from typing import List, Optional
from pydantic import BaseModel

class NetworkNode(BaseModel):
    id: str
    label: str
    group: str
    source: Optional[str] = None

class NetworkEdge(BaseModel):
    from_node: str # 'from' is a reserved keyword in Python, using from_node map to 'from' in export if needed
    to_node: str # 'to'

class NetworkData(BaseModel):
    nodes: List[NetworkNode]
    edges: List[dict] # Using dict for edges to easily support "from" key which is reserved in Python models if not careful with aliases
