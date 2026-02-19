from fastapi import APIRouter
from app.services.entity_service import EntityService
from typing import List

router = APIRouter(prefix="/sources", tags=["sources"])
entity_service = EntityService()

class SourceResponse:
    def __init__(self, id: str, label: str, description: str, count: int):
        self.id = id
        self.label = label
        self.description = description
        self.count = count

@router.get("/", response_model=List[dict])
def list_sources():
    """List all data sources with counts"""
    return entity_service.list_sources()
