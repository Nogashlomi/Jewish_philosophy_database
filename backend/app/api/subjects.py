from typing import List
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.subject import SubjectList, SubjectDetail

router = APIRouter()

@router.get("/", response_model=List[SubjectList])
async def list_subjects_json():
    """
    Get a list of all subjects.
    """
    return entity_service.list_subjects()

@router.get("/{subject_id}", response_model=SubjectDetail)
async def get_subject_detail_json(subject_id: str):
    """
    Get detailed information about a specific subject.
    """
    subject = entity_service.get_subject_detail(subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject
