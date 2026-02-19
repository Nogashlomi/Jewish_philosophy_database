from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.services.entity_service import entity_service
from app.schemas.person import PersonList, PersonDetail

router = APIRouter()

from fastapi import Query

@router.get("/", response_model=List[PersonList])
async def list_persons_json(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get a list of all historical persons with summary data.
    """
    return entity_service.list_persons(source=source)

@router.get("/{person_id}", response_model=PersonDetail)
async def get_person_detail_json(person_id: str):
    """
    Get detailed information about a specific person.
    """
    person = entity_service.get_person_detail(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person
