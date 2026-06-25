from fastapi import APIRouter
from typing import List, Dict, Any
from app.services.entity_service import entity_service

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_sources():
    return entity_service.get_sources()
