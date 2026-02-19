from fastapi import APIRouter, Query
from typing import Optional
from app.services.entity_service import entity_service
from app.schemas.network import NetworkData

router = APIRouter()

@router.get("/", response_model=NetworkData)
async def get_network_graph(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get nodes and edges for network visualization.
    """
    return entity_service.get_network_data(source=source)
