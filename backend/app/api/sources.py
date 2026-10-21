from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.core.auth import get_current_user
from app.services.entity_service import entity_service, ConflictError
from app.schemas.source import SourceInput, SourceDetail

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_sources():
    return entity_service.get_sources()

@router.post("/", response_model=SourceDetail, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_source(body: SourceInput):
    return entity_service.create_source(body)

@router.put("/{source_id}", response_model=SourceDetail, dependencies=[Depends(get_current_user)])
async def update_source(source_id: str, body: SourceInput):
    try:
        return entity_service.update_source(source_id, body)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
async def delete_source(source_id: str):
    try:
        entity_service.delete_source(source_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
