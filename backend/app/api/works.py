from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.work import WorkDetail

router = APIRouter()

@router.get("/")
async def list_works_json(
    source: Optional[str] = Query(None, description="Filter by data source ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
):
    """
    Get a paginated list of historical works with summary data.
    """
    return entity_service.list_works(source=source, page=page, page_size=page_size)

@router.get("/{work_id}", response_model=WorkDetail)
async def get_work_detail_json(work_id: str):
    """
    Get detailed information about a specific historical work.
    """
    work = entity_service.get_work_detail(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work
