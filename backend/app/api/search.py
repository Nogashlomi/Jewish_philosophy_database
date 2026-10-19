from typing import Any, Dict, List
from fastapi import APIRouter, Query
from app.services.entity_service import entity_service

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def search(
    q: str = Query(..., min_length=1, description="Text to search for"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
):
    return entity_service.search(q, limit)
