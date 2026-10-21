from typing import List
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.auth import get_current_user
from app.services.entity_service import entity_service
from app.schemas.place import PlaceList, PlaceDetail, PlaceInput

router = APIRouter()

@router.get("/", response_model=List[PlaceList])
async def list_places_json():
    """
    Get a list of all places.
    """
    return entity_service.list_places()

@router.post("/", response_model=PlaceList, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_place(body: PlaceInput):
    return entity_service.create_place(body)

@router.get("/geojson", response_model=dict)
async def get_places_geojson():
    """
    Get all places as a GeoJSON FeatureCollection.
    """
    return entity_service.get_geo_json()

@router.get("/translations/flows", response_model=list)
async def get_translation_flows():
    """
    Get all translation flows between places.
    """
    return entity_service.get_translation_flows()

@router.get("/{place_id}", response_model=PlaceDetail)
async def get_place_detail_json(place_id: str):
    """
    Get detailed information about a specific place.
    """
    place = entity_service.get_place_detail(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
