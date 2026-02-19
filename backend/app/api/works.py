from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.services.entity_service import entity_service
from app.schemas.work import WorkList, WorkDetail

router = APIRouter()

from fastapi import Query

@router.get("/", response_model=List[WorkList])
async def list_works_json(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get a list of all historical works with summary data.
    """
    return entity_service.list_works(source=source)

@router.get("/{work_id}", response_model=WorkDetail)
async def get_work_detail_json(work_id: str):
    """
    Get detailed information about a specific historical work.
    """
    work = entity_service.get_work_detail(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work
