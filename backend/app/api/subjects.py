from typing import List
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.subject import SubjectList, SubjectDetail

router = APIRouter()

@router.get("/", response_model=List[SubjectList])
async def list_subjects_json(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get a list of all subjects.
    """
    return entity_service.list_subjects(source=source)

@router.get("/{subject_id}", response_model=SubjectDetail)
async def get_subject_detail_json(subject_id: str):
    """
    Get detailed information about a specific subject.
    """
    subject = entity_service.get_subject_detail(subject_id)
    # The service returns a SubjectDetail with works list even if "not found" logic isn't explicit relative to 404
    # Because a subject ID might be valid but have no label. 
    # But usually we want to return 404 if it truly doesn't exist. 
    # The service currently constructs it even if label is just ID.
    # We can rely on that for now.
    return subject
