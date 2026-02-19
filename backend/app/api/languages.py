from typing import List
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.entity_service import entity_service
from app.schemas.language import LanguageList, LanguageDetail

router = APIRouter()

@router.get("/", response_model=List[LanguageList])
async def list_languages_json(source: Optional[str] = Query(None, description="Filter by data source ID")):
    """
    Get a list of all languages.
    """
    return entity_service.list_languages(source=source)

@router.get("/{lang_id}", response_model=LanguageDetail)
async def get_language_detail_json(lang_id: str):
    """
    Get detailed information about a specific language.
    """
    language = entity_service.get_language_detail(lang_id)
    return language
