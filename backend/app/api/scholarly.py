from typing import List
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.scholarly import ScholarlyList, ScholarlyDetail

router = APIRouter()

@router.get("/", response_model=List[ScholarlyList])
async def list_scholarly_works_json(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get a list of all scholarly works.
    """
    return entity_service.list_scholarly_works(source=source)

@router.get("/{work_id}", response_model=ScholarlyDetail)
async def get_scholarly_detail_json(work_id: str):
    """
    Get detailed information about a specific scholarly work.
    """
    work = entity_service.get_scholarly_detail(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Scholarly work not found")
    return work
