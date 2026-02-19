from fastapi import APIRouter, HTTPException
from typing import List
from app.services.entity_service import entity_service
from app.schemas.source import Source

router = APIRouter()

@router.get("/", response_model=List[Source])
def get_sources():
    """
    Get all data sources with their scholarly work counts.
    """
    return entity_service.list_sources()
