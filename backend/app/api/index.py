from fastapi import APIRouter
from app.services.entity_service import entity_service

router = APIRouter()

from typing import Optional
from fastapi import Query

@router.get("/stats")
async def get_stats(source: Optional[str] = Query(None, description="Filter by data source ID")):
    return entity_service.get_global_stats(source=source)
