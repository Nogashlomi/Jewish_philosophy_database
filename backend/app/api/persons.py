from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_current_user
from app.services.entity_service import entity_service, ConflictError
from app.schemas.person import PersonDetail, VerifyName, UpdateConnections

router = APIRouter()

@router.get("/")
async def list_persons_json(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by data source ID"),
    search: Optional[str] = Query(None, description="Search term to filter by name")
):
    """
    Get a paginated list of historical persons with summary data.
    """
    return entity_service.list_persons(page=page, page_size=page_size, source=source, search=search)

@router.get("/{person_id}", response_model=PersonDetail)
async def get_person_detail_json(person_id: str):
    """
    Get detailed information about a specific person.
    """
    person = entity_service.get_person_detail(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@router.post("/{person_id}/name/verify", response_model=PersonDetail, dependencies=[Depends(get_current_user)])
async def verify_person_name(person_id: str, body: VerifyName):
    try:
        return entity_service.verify_name(person_id, body.name, body.viaf_id, body.alt_names)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{person_id}/connections", response_model=PersonDetail, dependencies=[Depends(get_current_user)])
async def update_person_connections(person_id: str, body: UpdateConnections):
    try:
        return entity_service.update_connections(person_id, body.connections)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
