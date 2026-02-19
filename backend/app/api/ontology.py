from fastapi import APIRouter
from app.services.entity_service import entity_service

router = APIRouter()

@router.get("/", response_model=dict)
async def get_ontology():
    """
    Get the ontology graph structure (classes as nodes, properties as edges).
    """
    return entity_service.get_ontology_graph()
