from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.person import PersonDetail

router = APIRouter()

@router.get("/")
async def list_persons_json(
    source: Optional[str] = Query(None, description="Filter by data source ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
):
    """
    Get a paginated list of historical persons with summary data.
    """
    return entity_service.list_persons(source=source, page=page, page_size=page_size)

@router.get("/{person_id}", response_model=PersonDetail)
async def get_person_detail_json(person_id: str):
    """
    Get detailed information about a specific person.
    """
    person = entity_service.get_person_detail(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
